#!/usr/bin/env python
import argparse
import copy
import subprocess
import re
import numpy as np
import os
import sys
import shutil
from pathlib import Path 
from scipy.optimize import minimize_scalar

src_path = os.path.join(os.path.dirname(__file__), "src")
sys.path.append(src_path)
from control import Control 
from system import System
from deck import Deck, read_params_and_deck
from zero_params import zero_var_params, save_opt_file

# -----------------------
# UTILITY FUNCTIONS:
# -----------------------

def change_working_directory():
    """Change the working directory to the script's directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Changed working directory to: {script_dir}")

def setup_environment():
    """Create necessary directories (`min`, `opt`) in the current working directory."""
    change_working_directory()
    cwd = Path.cwd()
    (cwd / "min").mkdir(exist_ok=True) # directory to store optimized decks
    (cwd / "opt").mkdir(exist_ok=True) # directory to store opt files

def load_system(name: str, target_ctrl_file: str, scattering_ctrl_file: str, three_bp: bool, E_start: float):
    """
    Create and return a System object.

    Args:
        name: Name of the system.
        target_ctrl_file: Absolute path to the target control file.
        scattering_ctrl_file: Absolute path to the system control file.
        three_bp: Flag to enable/disable three-body potential.
        E_start: Initial energy value for scattering optimization.

    Returns:
        Initialized System object.
    """
    return System(name, target_ctrl_file, scattering_ctrl_file, three_bp, E_start)

def get_build_bins():
    """ Locate and validate paths to the energy and optimize binaries."""
    setup_environment()
    base_dir = os.path.dirname(os.path.dirname(os.getcwd())) # build bin located two directories up
    energy_bin = os.path.join(base_dir, "build/bin/energy")
    optimize_bin = os.path.join(base_dir, "build/bin/optimize")
    print(f"Using energy binary: {energy_bin}")
    
    if not os.path.exists(energy_bin) or not os.path.exists(optimize_bin):
        raise FileNotFoundError("Energy or optimize binary not found in build directory.")
    
    return energy_bin, optimize_bin

ENERGY_BIN, OPTIMIZE_BIN = get_build_bins()

# -----------------------
# MAIN AUTO_OPT LOGIC:
# -----------------------

def main(system: System):

    target_control = system.target_control
    target_ctrl = system.target_ctrl_file
    scattering_control = system.scattering_control
    scattering_ctrl = system.scattering_ctrl_file
    
    target_param_file = target_control.parameters['wf'].param_file.strip("'\"")

    # STEP 1: Optimize target deck (he4) to get optimized parameters
    target_energy, target_energy_var = optimize_deck(target_ctrl)                   # saves opt deck to min/
    print(f"Optimized target energy: {target_energy:.4f} MeV, variance: {target_energy_var:.4f}")
    opt_target_deck, _ = read_params_and_deck(target_param_file, target_control.parameters['optimized_deck'].strip("'\""))

    # make temp file for working deck (he5)
    wf = scattering_control.parameters.get('wf', None)
    if wf is None:
        raise RuntimeError("No wavefunction block found in control file.")
    shutil.copy(wf.deck_file.strip("'\""), "temp.dk")                               # use temp.dk to update params instead of original deck
    setattr(wf, 'deck_file', "'temp.dk'")                                           # update deck file in control
    scattering_control.write_control()
    working_deck = wf.deck_file.strip("'\"")
    print(f"Working deck file: {working_deck}")
    param_file = wf.param_file.strip("'\"")

    scattering_deck, scattering_deck_name = read_params_and_deck(param_file, working_deck)

    # copy optimized params from target deck to scattering deck (lines 4-19)
    params_to_skip = ['Name', 'PI', 'J', 'MJ', 'T', 'MT', 'lwf', 'lsc', 'l3bc', 'lcut']
    for target_param, scattering_param in zip(opt_target_deck.parameters.keys(), scattering_deck.parameters.keys()):
        if target_param not in params_to_skip and target_param == scattering_param or target_param in ['cutR', 'cutA', 'cutW', 'delta', 'eps', 'theta', 'ups',]: # 'diff names for [] in opt_deck
            scattering_deck.parameters[scattering_param] = opt_target_deck.parameters[target_param]
    scattering_deck.write_deck(scattering_deck_name) 


    # STEP 2: Find starting bscat value (bscat yielding E_rel ~ 3 MeV)
    initial_bscat = minimize_scalar(find_starting_bscat, args=(target_energy, system, scattering_deck), bounds=(-0.15, 0.15), method='bounded', options={'maxiter': 10}).x  # Find bscat that gives E_rel close to E_start
    print(f"Initial bscat found: {initial_bscat:.4f}")
    scattering_deck.parameters['1S[0]'].bscat = initial_bscat
    scattering_deck.write_deck(scattering_deck_name)                                      # Update bscat in deck
    scattering_deck.parameters['1S[0]'].wse = calculate_energy_com(extract_final_energy(run_energy(scattering_ctrl)), target_energy) - 0.5
    scattering_deck.write_deck(scattering_deck_name)                         # Set wse based on closest E_rel
    print(f"Setting wse to {scattering_deck.parameters['1S[0]'].wse:.4f} based on initial bscat {initial_bscat:.4f}")

    # STEP 3: Generate optimized decks for range of bscat values
    down, up = clustered_grid(start=initial_bscat, min_val=-2, max_val=2, n=40) 
    print("Downward grid:", down)
    print("Upward grid with start:", up)
    up_results = iterate_bscat(scattering_control, up, "min", target_energy)
    scattering_control.parameters['wf'].deck_file = f"'{working_deck}'"                   # Reset deck file in control
    scattering_control.write_control()
    down_results = iterate_bscat(scattering_control, down[::-1], "min", target_energy)    # Reverse grid for downward iteration

    # STEP 4: Save results to CSV file
    with open(f"optimized_decks_{initial_bscat:.4f}.csv", "w") as f:
        cwd = Path.cwd()
        f.write("system, channel, potential, bscat, wse, E_relative, var, path_to_deck\n")
        for res in up_results + down_results:
            bscat, wse, E_rel, var, path = res
            f.write(f"{system.name}, {system.channels[0]}, {system.potentials[0]}, {bscat:.4f}, {wse:.4f}, {E_rel:.4f}, {var:.4f}, {os.path.join(cwd, path)}\n")

    clean_dir(system)  # Clean up working directory after processing


def optimize_deck(control_file):
    """Run optimization using the provided control file."""
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

def calculate_energy_com(energy_system, target_energy):
    return energy_system - target_energy

def find_starting_bscat(bscat, target_energy, system, scattering_deck):
    # Run energy calculation
    scattering_deck.parameters['1S[0]'].bscat = bscat
    scattering_deck.write_deck("temp")
    E_system = extract_final_energy(run_energy(system.scattering_ctrl_file))
    E_rel = calculate_energy_com(E_system, target_energy)
    print(bscat, E_rel)
    return abs(E_rel - system.E_start)
    


def iterate_bscat(control: Control, grid: np.ndarray, working_dir, he4_energy):
    """
    Iterate over bscat values to optimize scattering wavefunction.

    Args:
        control: Control object for the scattering system.
        grid: Array of bscat values to scan.
        working_dir: Directory to store output decks.
        he4_energy: Reference energy of target.

    Returns:
        List of tuples: (bscat, final_wse, E_rel, variance, deck_path).
    """

    results = []

    # Backup the initial (or last known good) state of control for restoration if needed
    last_good_control = copy.deepcopy(control)
    param_file = control.parameters['wf'].param_file.strip("'\"")

    for bscat in grid:
        deck_file = control.parameters['wf'].deck_file.strip("'\"")
        deck, deck_name = read_params_and_deck(param_file, deck_file)
        print(f"Using deck file: {deck_file}")
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
        if E_rel < 0.25 or E_rel > 6.5:
            print(f"Skipping bscat={bscat:.4f} due to E_rel={E_rel:.4f} out of bounds.")
            control = copy.deepcopy(last_good_control)
            continue
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
        if E_rel < 0.25 or E_rel > 6.5:
            print(f"Skipping bscat={bscat:.4f} due to E_rel={E_rel:.4f} out of bounds.")
            control = copy.deepcopy(last_good_control)
            continue
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
            control = copy.deepcopy(last_good_control)
            continue

        # Update the backup copy to the current successful state.
        last_good_control = copy.deepcopy(control)

    return results

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

def clean_dir(system):
    """Clean up working files and control files in working directory."""
    shutil.rmtree(Path("opt"), ignore_errors=True)
    os.remove("temp.dk")
    os.remove(system.scattering_ctrl_file)
    os.remove(system.target_ctrl_file)
        
# -----------------------
# COMMAND LINE INTERFACE:
# -----------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Run AutoOpt using system parameters from the command line.",
        epilog="""\
            Example:
            python AutoOpt.py --name He4n \
                --target /path/to/he4_copy.ctrl \
                --scattering /path/to/he4n_copy.ctrl \
                --three_bp False \
                --E_start 3.0
            """
    )
    parser.add_argument('--name', required=True, help="Name of the system (e.g., He4n).")
    parser.add_argument('--target', required=True, help="Absolute path to the target control file.")
    parser.add_argument('--scattering', required=True, help="Absolute path to the scattering control file.")
    parser.add_argument('--three_bp', type=lambda s: s.lower() in ['true', '1', 'yes'], required=True,
                        help="Enable three-body potential? (True/False)")
    parser.add_argument('--E_start', type=float, required=True, help="Starting energy (in MeV).")
    args = parser.parse_args()

    # Create the System object from CLI parameters
    system_obj = load_system(
        name=args.name,
        target_ctrl_file=args.target,
        scattering_ctrl_file=args.scattering,
        three_bp=args.three_bp,
        E_start=args.E_start
    )
    print(f"System '{system_obj.name}' successfully initialized.")
    
    # Execute the main auto-optimization routine
    main(system_obj)


