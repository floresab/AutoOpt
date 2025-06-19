import subprocess
import re
import numpy as np
import os
import sys
import shutil
from pathlib import Path 
import copy

sys.path.append("/Users/lydiamazeeva/QMC/nQMCC/nQMCC/external/nQMCC_Scripts/src")
from control import Control
from deck import Deck, read_params_and_deck
from zero_params import zero_var_params, save_opt_file

ENERGY_BIN = "/Users/lydiamazeeva/QMC/nQMCC/nQMCC/build/bin/energy"
OPTIMIZE_BIN = "/Users/lydiamazeeva/QMC/nQMCC/nQMCC/build/bin/optimize"

system = "He4n"
channel = "1/2+"
potential = "AV18"
target_ctrl = "/Users/lydiamazeeva/QMC/nQMCC/nQMCC/external/nQMCC_Scripts/he4.ctrl"
scattering_ctrl = "/Users/lydiamazeeva/QMC/nQMCC/nQMCC/external/nQMCC_Scripts/he4n.ctrl"
E_start = 3.0 # MeV, used for intial bscat guess    


def main():
    os.chdir("/Users/lydiamazeeva/QMC/nQMCC/nQMCC/external/nQMCC_Scripts")  # Change to script directory
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
        raise RuntimeError("No wavefunction block found in control file.")
    print(wf.deck_file.strip("'\""))
    shutil.copy(wf.deck_file.strip("'\""), "/Users/lydiamazeeva/QMC/nQMCC/nQMCC/external/nQMCC_Scripts/temp.dk")

    setattr(wf, 'deck_file', "'/Users/lydiamazeeva/QMC/nQMCC/nQMCC/external/nQMCC_Scripts/temp.dk'")                                           # update deck file in control
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
    system_deck.write_deck(system_deck_name) 


    # STEP 2: Find starting bscat value (bscat yielding E_rel ~ 3 MeV)
    intial_bscat_search_grid = generate_symmetric_grid(-0.15, 0.15, num_points=4, power=2.0)
    initial_bscat, closest_E_rel = find_starting_bscat(param_file, working_deck, intial_bscat_search_grid, he4_energy) 


    system_deck.parameters['1S[0]'].wse = closest_E_rel - 0.5  # Set wse based on closest E_rel
    system_deck.write_deck(system_deck_name)  # Save updated deck with wse

    # STEP 4: Generate optimized decks for range of bscat values
    down, up = clustered_grid(start=initial_bscat, min_val=-2, max_val=2, n=4)
    print("Downward grid:", down)
    print("Upward grid with start:", up)
    up_results = iterate_bscat(control, up, "min", he4_energy)
    control.parameters['wf'].deck_file = f"'{working_deck}'"  # Reset deck file in control
    control.write_control()
    down_results = iterate_bscat(control, down[::-1], "min", he4_energy)  # Reverse for downward iteration



    with open(f"optimized_inputs_{initial_bscat:.4f}.csv", "w") as f:
        f.write("system, channel, potential, bscat, wse, E_relative, var, path_to_deck\n")
        for res in up_results + down_results:
            bscat, wse, E_rel, var, path = res
            f.write(f"{system}, {channel}, {potential}, {bscat:.4f}, {wse:.4f}, {E_rel:.4f}, {var:.4f}, {path}\n")


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
        print("Could not find optimized energy and variance.")
        return None, None


def extract_final_energy(output):
    matches = re.findall(r'H\s*=\s*([-+]?\d+\.\d+)', output)
    return float(matches[-1]) if matches else None

def calculate_energy_com(energy_system, ctrl_energy):
    return energy_system - ctrl_energy


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

    print(f"Best bscat: {start_bscat:.4f} yielding E_rel ≈ {closest_E_rel:.6f} MeV")
    return start_bscat, closest_E_rel



def iterate_bscat(control: Control, grid: np.ndarray, working_dir, he4_energy):

    results = []

    param_file = control.parameters['wf'].param_file.strip("'\"")

    for bscat in grid:
        deck_file = control.parameters['wf'].deck_file.strip("'\"")
        deck, deck_name = read_params_and_deck(param_file, deck_file)
        print(f"\n🔁 Starting bscat = {bscat:.4f}")
        
        # 1. Load and update deck
        deck.parameters['1S[0]'].bscat = bscat
        deck.write_deck(deck_file.strip(".dk"))
        
        # 2. Run energy calculation to determine wse
        E_system = extract_final_energy(run_energy(control.Name + ".ctrl"))
        if E_system is None:
            print(f"Could not get energy for bscat={bscat:.4f}")
            continue

        E_rel = calculate_energy_com(E_system, he4_energy)
        wse_val = E_rel - 0.5
        if E_rel < 0.5 or E_rel > 6.5:
            print(f"Skipping bscat={bscat:.4f} due to E_rel={E_rel:.4f} out of bounds.")
            break
        print(f"bscat = {bscat:.4f}, E_rel = {E_rel:.4f}, setting wse = {wse_val:.4f}")

        # 3. Set wse in deck
        deck.parameters['1S[0]'].wse = wse_val
        deck.write_deck(deck_file.strip(".dk"))

        # Generate opt file for He5 correlations
        zero_deck, _ = zero_var_params(
            param_file,
            deck_file,
            '1S[0]',
            [['spu', 'spv', 'spr', 'spa', 'spb', 'spc', 'spk', 'spl'], ['wsr', 'wsa']],
            default=0.20
        )

        # Save opt input for He5 and update control
        opt_path_he5 = save_opt_file(zero_deck, f"{deck_name}_{bscat*10000:.4f}", "./opt", wse_flag=False)
        print(f"Generated opt file for He5 correlations: {opt_path_he5}")
        control.parameters['optimization_input'] = f"'{opt_path_he5}'"
        control.write_control()

        # 5. Define new deck filename and update control
        deck_basename = f"opt_he4n_av18_{bscat:.4f}.dk"
        optimized_deck_path = Path(working_dir) / deck_basename
        control.parameters['optimized_deck'] = f"'{optimized_deck_path}'"
        control.write_control()

        # 6. Run optimization with He5 correlations
        try:
            energy, variance = optimize_deck(control.Name + ".ctrl")
        except RuntimeError as e:
            print(f"Error during optimization for bscat={bscat:.4f}: {e}")
            continue
        E_rel = calculate_energy_com(energy, he4_energy)
        print(f"He5 opt: bscat = {bscat:.4f}, E_rel = {E_rel:.4f}, var = {variance:.4f}")

        # 7. Generate opt input for wse only
        zero_deck, _ = zero_var_params(param_file, deck_file, '1S[0]', [['wse']], default=0.20)
        wse_opt_path = save_opt_file(zero_deck, f"{deck_name}_{bscat*10000:.4f}", "./opt", wse_flag=True)
        print(f"Generated wse opt file: {wse_opt_path}")

        # 8. Update control file with new optimization input
        control.parameters['wf'].deck_file = f"'{optimized_deck_path}'" # use optimized deck
        print(f"Updated control file with optimized deck: {optimized_deck_path}")
        control.parameters['optimization_input'] = f"'{wse_opt_path}'"
        control.write_control()

        # 9. Final optimization; updates otimized deck
        energy, variance = optimize_deck(control.Name + ".ctrl")
        final_E_rel = calculate_energy_com(energy, he4_energy)
        print(f"Final opt: bscat = {bscat:.4f}, final E_rel = {final_E_rel:.4f}, var = {variance:.4f}")

        final_optimized_deck, _ = read_params_and_deck(param_file, optimized_deck_path)
        final_wse = final_optimized_deck.parameters['1S[0]'].wse

        # 10. Save results
        results.append((bscat, final_wse, final_E_rel, variance, str(optimized_deck_path)))

        if final_E_rel < 0.5 or final_E_rel > 6.0:
            print(f"Skipping bscat={bscat:.4f} due to E_rel={final_E_rel:.4f} out of bounds.")
            break

    return results


def generate_symmetric_grid(min_val, max_val, num_points=50, power=2.0):
    """
    Generates a grid from min_val to max_val (excluding 0),
    with denser spacing near 0 using a power-law distribution.
    
    Returns:
        np.ndarray: Array of grid points.
    """
    assert min_val < 0 and max_val > 0, "min_val must be < 0 and max_val > 0"
    half_points = num_points // 2

    x = np.linspace(0, 1, half_points + 1)[1:] 
    positive = x ** power * max_val
    negative = -1 * (x ** power * abs(min_val))

    return np.concatenate([negative[::-1], positive])

def clustered_grid(start: float, min_val: float, max_val: float, n: int = 10) -> tuple[np.ndarray, np.ndarray]:
    """
    Generate clustered grid points upward and downward from `start`,
    with higher density near `start`, bounded by `min_val` and `max_val`.

    Parameters:
        start (float): Starting value to cluster around.
        min_val (float): Minimum value allowed (exclusive).
        max_val (float): Maximum value allowed (exclusive).
        n (int): Number of points in each direction (not counting the `start` in upward grid).

    Returns:
        Tuple of (downward_grid, upward_grid_with_start)
    """
    if not (min_val < start < max_val):
        raise ValueError("start must be between min_val and max_val")

    # Logarithmic scaling for spacing
    log_space = np.geomspace(1e-2, 1.0, n)

    # DOWNWARD grid
    down_steps = (start - min_val) * log_space
    downward = start - down_steps[::-1]
    downward = downward[downward > min_val]

    # UPWARD grid (excluding start)
    up_steps = (max_val - start) * log_space
    upward = start + up_steps
    upward = upward[upward < max_val]

    # Include start at the beginning of the upward grid
    upward_with_start = np.insert(upward, 0, start)

    return downward, upward_with_start
        

main()

