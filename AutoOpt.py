import subprocess
import re
import numpy as np
import os
import sys
import shutil
from pathlib import Path 

sys.path.append("/Users/lydiamazeeva/QMC/nQMCC_Scripts")
from control import Control
from deck import Deck, read_params_and_deck
from zero_params import zero_var_params, save_opt_file

ENERGY_BIN = "./build/bin/energy"
OPTIMIZE_BIN = "./build/bin/optimize"

system = "He4n"
channel = "1/2+"
potential = "AV18"
target_ctrl = "he4.ctrl"
scattering_ctrl = "he4n.ctrl"
E_start = 3.0 # MeV, used for intial bscat guess    



def main():
    # STEP 1: Optimize target (He4) ground state 
    target_control = Control()
    target_control.read_control(target_ctrl)
    target_param_file = target_control.parameters['wf'].param_file.strip("'\"")

    he4_energy, he4_energy_var = optimize_deck(target_ctrl)                     # saves opt deck to min/
    # he4_energy = -23.742
    opt_target_deck, _ = read_params_and_deck(target_param_file, target_control.parameters['optimized_deck'].strip("'\""))
    # opt_target_deck, _ = read_params_and_deck('nuclei/params/he4.params', 'min/opt_he4_av18_uix.dk')
    

    # copy optimized params of target (he4) to working deck (he5)
    control = Control()
    control.read_control(scattering_ctrl)

    wf = control.parameters.get('wf', None)
    working_deck_path = wf.deck_file.strip("'\"") if wf else None                    # save path for generating opt file
    if wf is None:
        raise RuntimeError("❌ No wavefunction block found in control file.")
    shutil.copy(wf.deck_file.strip("'\""), "temp.dk")

    setattr(wf, 'deck_file', "'temp.dk'")                                           # update deck file in control
    control.write_control()
    working_deck = wf.deck_file.strip("'\"")
    param_file = wf.param_file.strip("'\"")

    system_deck, system_deck_name = read_params_and_deck(param_file, working_deck)
    # system_deck, system_deck_name = read_params_and_deck('nuclei/params/he4n.params', 'nuclei/decks/He/5/he5_1hp_av18.dk')

    # copy optimized params from target deck to system deck (lines 4-19)
    params_to_skip = ['Name', 'PI', 'J', 'MJ', 'T', 'MT', 'lwf', 'lsc', 'l3bc', 'lcut']
    for target_param, system_param in zip(opt_target_deck.parameters.keys(), system_deck.parameters.keys()):
        if target_param not in params_to_skip and target_param == system_param or target_param in ['cutR', 'cutA', 'cutW']: # 'diff names for [] in opt_deck
            system_deck.parameters[system_param] = opt_target_deck.parameters[target_param]
    # system_deck.write_deck(system_deck_name)
    system_deck.write_deck("temp") 


    # STEP 2: Find starting bscat value (bscat yielding E_rel ~ 3 MeV)
    intial_bscat_range_negative = np.linspace(-0.15, -0.10, 10)
    start_bscat_neg, closest_E_rel_neg = find_starting_bscat(param_file, working_deck, intial_bscat_range_negative, he4_energy)

    intial_bscat_range_positive = np.linspace(0.0, 0.1, 10)
    start_bscat_pos, closest_E_rel_pos = find_starting_bscat(param_file, working_deck, intial_bscat_range_positive, he4_energy)


    # STEP 3: Generate opt file for He5 
    params_to_optimize = ['spu','spv','spr','spa', 'spb', 'spc', 'spk', 'spl'] # param group of ss object
    zero_deck, _ = zero_var_params(param_file, "temp.dk", '1S[0]', params_to_optimize, default=0.20)  # Zero out all float params in deck

    opt_path = save_opt_file(zero_deck, working_deck_path, "./opt")

    # change optimization_input in control file
    control.parameters['optimization_input'] = f"'{opt_path}'"
    control.write_control()


    # STEP 4: Generate optimized decks for range of bscat values


    # Negative bscat values
    results_neg_increase = iterate_bscat_direction(
        control=control,
        start_bscat=start_bscat_neg, 
        closest_E_rel=closest_E_rel_neg,
        magnitude_change="decrease", 
        target_energy_limit= 0.25, 
        working_dir='min', 
        he4_energy=he4_energy
    )
    results_neg_decrease = iterate_bscat_direction(
        control=control,
        start_bscat=start_bscat_neg, 
        closest_E_rel=closest_E_rel_neg,
        magnitude_change="increase", 
        target_energy_limit= 6.0, 
        working_dir='min', 
        he4_energy=he4_energy
    )
    # Positive bscat values
    results_pos_increase = iterate_bscat_direction(
        control=control,
        start_bscat=start_bscat_pos, 
        closest_E_rel=closest_E_rel_pos,
        magnitude_change="increase", 
        target_energy_limit= 6.0, 
        working_dir='min', 
        he4_energy=he4_energy
    )
    results_pos_decrease = iterate_bscat_direction(
        control=control,
        start_bscat=start_bscat_pos, 
        closest_E_rel=closest_E_rel_pos,
        magnitude_change="decrease", 
        target_energy_limit= 0.25, 
        working_dir='min', 
        he4_energy=he4_energy
    )

    with open(f"optimized_inputs_{start_bscat_neg}.csv", "w") as f:
        f.write("system,channel,potential,bscat,wse,path_to_deck,E_relative,var\n")
        for res in up_results + down_results:
            bscat, wse, path, E_rel, var = res
            f.write(f"{system},{channel},{potential},{bscat:.4f},{wse:.4f},{path},{E_rel:.4f},{var:.4f}\n")


    

# Returns the optimized energy and variance from the output of the optimization command.
# Saves opt deck to path specified in control file.
def optimize_deck(control_file):
    cmd = ["mpirun", "-np", "8", OPTIMIZE_BIN]
    output_text = run_command(cmd, control_file)
    energy, variance = extract_opt_energy(output_text)
    if energy is None or variance is None:
        raise RuntimeError(f"Failed to extract optimized energy from control file: {control_file}")
    return energy, variance


def run_command(cmd, input_file):
    with open(input_file, "r") as ctrl:
        result = subprocess.run(cmd, stdin=ctrl, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    # print(f"Command output: {result.stdout}")
    return result.stdout

def run_energy(ctrl_file):
    """Run energy calculation for He4+n."""
    cmd = ["mpirun", "-np", "8", ENERGY_BIN]
    output_text = run_command(cmd, ctrl_file)
    return output_text

def extract_opt_energy(output_text):
    match = re.search(r'OPTIMIZED ENERGY:\s*([-+]?[0-9]*\.?[0-9]+)\s*\(([-+]?[0-9]*\.?[0-9]+)\)', output_text)
    if match:
        energy = float(match.group(1))
        variance = float(match.group(2))
        return energy, variance
    else:
        print("❌ Could not find optimized energy and variance.")
        return None, None


def extract_final_energy(output):
    matches = re.findall(r'H\s*=\s*([-+]?\d+\.\d+)', output)
    return float(matches[-1]) if matches else None

def calculate_energy_com(energy_system, ctrl_energy):
    return energy_system - ctrl_energy

def save_file(deck, deck_name, base_dir="temp"):
    os.makedirs(base_dir, exist_ok=True)
    deck.write_deck(os.path.join(base_dir, deck_name + "_temp"))


def find_starting_bscat(param_file, working_deck, bscat_range, he4_energy):
    start_bscat = None
    closest_E_rel = None
    min_diff = float('inf')

    for bscat in bscat_range:
        # Load deck
        deck, deck_name = read_params_and_deck(param_file, working_deck)

        # Update bscat parameter
        deck.parameters['1S[0]'].bscat = bscat
        deck.write_deck(deck_name)

        # Run energy calculation
        E_system = extract_final_energy(run_energy(scattering_ctrl))
        E_rel = calculate_energy_com(E_system, he4_energy)

        diff = abs(E_rel - E_start)
        print(f"bscat: {bscat:.4f}, E_rel: {E_rel:.6f}, diff: {diff:.6f}")

        if diff < min_diff:
            min_diff = diff
            start_bscat = bscat
            closest_E_rel = E_rel

    print(f"\n✅ Best bscat: {start_bscat:.4f} yielding E_rel ≈ {closest_E_rel:.6f} MeV")
    return start_bscat, closest_E_rel


def iterate_bscat_direction(control: Control, start_bscat, closest_E_rel, magnitude_change, target_energy_limit, working_dir, he4_energy):
    """Iterate over bscat values in the specified direction."""
    param_file = control.parameters['wf'].param_file.strip("'\"")
    deck_file = control.parameters['wf'].deck_file.strip("'\"")
    deck, deck_name = read_params_and_deck(param_file, deck_file)

    # set initial bscat and E_rel
    deck.parameters['1S[0]'].bscat = start_bscat
    deck.parameters['1S[0]'].wse = closest_E_rel - 0.5  # Set initial wse to closest E_rel - 0.5 MeV
    deck.write_deck(deck_name)
    
    current_bscat = start_bscat
    results = []

    def scale_bscat(bscat, magnitude_change):
        sign = 1 if bscat >= 0 else -1
        magnitude = abs(bscat)

        if magnitude_change == "increase":
            magnitude *= 1.15
        else:
            magnitude *= 0.85

        return sign * magnitude

    # First iteration
    deck_basename = f"opt_he4n_av18_{current_bscat:+.4f}.dk"
    optimized_deck_path = Path(working_dir) / deck_basename                             # min/opt_he4n_av18_0.1000_uix.dk


    # Update control file
    control.parameters['optimized_deck'] = f"'{optimized_deck_path}'"
    control.write_control()


    # Run optimization
    energy, variance = optimize_deck(control.Name + ".ctrl")
    E_rel = calculate_energy_com(energy, he4_energy)

    results.append((current_bscat, E_rel, variance, str(optimized_deck_path)))
    
    count = 0

    while True and count < 10:
        # Load previous deck
        # prev_deck, _ = read_params_and_deck(param_file, str(optimized_deck_path.parent / deck_basename))
        current_bscat = scale_bscat(current_bscat, magnitude_change)

        deck_basename = f"opt_he4n_av18_{current_bscat:+.4f}.dk"
        optimized_deck_path = Path(working_dir) / deck_basename 

    
        # Update bscat in deck
        deck.parameters['1S[0]'].bscat = current_bscat
        deck.write_deck(deck_name)
        # Run energy to find wse
        E_system = extract_final_energy(run_energy(scattering_ctrl))
        if E_system is None:
            print(f"❌ Could not extract energy for bscat={current_bscat:.4f}. Skipping...")
            count += 1
            continue
        wse = calculate_energy_com(E_system, he4_energy)
        print(f"bscat: {current_bscat:.4f}, wse: {wse:.4f}")
        deck.parameters['1S[0]'].wse = wse - 0.5  # Set wse to calculated value - 0.5 MeV
        deck.write_deck(deck_name)

        # Update control again
        control.parameters['optimized_deck'] = f"'{optimized_deck_path}'"
        control.write_control()

        try:
            # Run optimization
            energy, variance = optimize_deck(control.Name + ".ctrl")
            E_rel = calculate_energy_com(energy, he4_energy)
        except RuntimeError as e:
            print(f"❌ Optimization failed at bscat={current_bscat:.4f}: {e}")
            count += 1
            continue


        print(f"bscat: {current_bscat:.4f}, E_rel: {E_rel:.4f}")

        # Stop condition
        stop_condition = (
            magnitude_change == "increase" and E_rel >= target_energy_limit or
            magnitude_change == "decrease" and E_rel <= target_energy_limit
        )

        if stop_condition:
            print(f"🛑 Stopping at bscat = {current_bscat:.4f}, E_rel = {E_rel:.6f}")
            break



        results.append((current_bscat, deck.parameters['1S[0]'].wse, str(optimized_deck_path), E_rel, variance))
        count += 1

    return results
        

# main()
