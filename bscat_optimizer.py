import sys
import os
import copy
import matplotlib.pyplot as plt
import json

src_path = os.path.join(os.path.dirname(__file__), "src")
sys.path.append(src_path)

from control import Control 
from deck import read_params_and_deck
from AutoOpt import opt_E

# --- Parameters ---
# target_energy = -23.8819
# slope_max = 2
# input_db = 0.01152 # 15% b_0
# input_de = 0.25
# Emin = 0.5
# Emax = 5.5
# Estart = 3
# b_0 = 0.0768

# --- Helper Functions ---
def estimate_initial_db_de(b_0, input_db, control_file, deck, deck_file, target_energy):
    b_plus = b_0 + input_db
    b_minus = b_0 - input_db

    control_forward = Control()
    control_forward.read_control(control_file)
    control_forward.Name = control_forward.Name + "_forward"
    control_forward.write_control()
    forward_file = control_forward.Name + ".ctrl"

    print("FORWARD (b_minus)")
    E_minus, *_ = opt_E(b_minus, forward_file, target_energy, "scratch")
    deck.write_deck(deck_file.strip(".dk"))

    control_backward = Control()
    control_backward.read_control(control_file)
    control_backward.Name = control_backward.Name + "_backward"
    control_backward.write_control()
    backward_file = control_backward.Name + ".ctrl"
    
    print("BACKWARD (b_plus)")
    E_plus, *_ = opt_E(b_plus, backward_file, target_energy, "scratch")
    deck.write_deck(deck_file.strip(".dk"))

    db_de = (b_plus - b_minus) / (E_plus - E_minus)
    return db_de, b_plus, E_plus, b_minus, E_minus, backward_file, forward_file

def update_db_de(b_new, b_prev, E_new, E_prev):
    return (b_new - b_prev) / (E_new - E_prev)

def log_step_info(step, direction, bscat, db_de, E_next):
    print(f"[{direction} Step {step}] bscat = {bscat:.5f}, db/de = {db_de:.5f}, E_rel = {E_next:.5f}")




def run_bscat_scan(control_file, b_0, input_db, input_de, Emin, Emax, Estart, target_energy, slope_max):
    
    E_0, var_0, path_0, wse_0 = opt_E(b_0, control_file, target_energy, "scratch")

    scattering_control = Control()
    scattering_control.read_control(control_file)

    param_file = scattering_control.parameters['wf'].param_file.strip("'\"")
    deck_file = scattering_control.parameters['wf'].deck_file.strip("'\"")
    deck, deck_name = read_params_and_deck(param_file, deck_file)

    results = [{
        "bscat": b_0,
        "E_rel": E_0,
        "variance": var_0,
        "deck_path": path_0,
        "wse": wse_0
    }]

    db_de_initial, b_plus, E_plus, b_minus, E_minus, backward_ctrl_file, forward_ctrl_file = estimate_initial_db_de(
        b_0, input_db, control_file, deck, deck_file, target_energy)

    
    print(f"Initial db/de = {db_de_initial:.5f} (b_plus = {b_plus:.5f}, E_plus = {E_plus:.5f}, b_minus = {b_minus:.5f}, E_minus = {E_minus:.5f})")

    # --- Forward Walk ---
    bscat = b_0
    b_prev = b_minus
    E_prev = E_minus
    num_samples_up = int((Emax - Estart) / input_de)
    db_de = db_de_initial

    print("Starting forward walk")


    for step in range(num_samples_up):
        b_next = bscat + (db_de * input_de)
        E_next, var_next, path_next, wse_next = opt_E(b_next, forward_ctrl_file, target_energy, "scratch")
        if E_next is None:
            break
        db_de = update_db_de(b_next, b_prev, E_next, E_prev)
        if db_de > 0:
            db_de *= -1
        log_step_info(step, "Forward", b_next, db_de, E_next)

        if E_next < Emin or E_next > Emax or abs(db_de) > slope_max:
            break

        results.append({
            "bscat": b_next,
            "E_rel": E_next,
            "variance": var_next,
            "deck_path": path_next,
            "wse": wse_next
        })

        bscat = b_next
        b_prev = b_next
        E_prev = E_next

    # --- Backward Walk ---
    bscat = b_0
    b_prev = b_plus
    E_prev = E_plus
    num_samples_down = int((Estart - Emin) / input_de)
    db_de = db_de_initial

    print("Starting backward walk")

    for step in range(num_samples_down):
        b_next = bscat - (db_de * input_de)
        E_next, var_next, path_next, wse_next = opt_E(b_next, backward_ctrl_file, target_energy, "scratch")
        if E_next is None:
            break
        db_de = update_db_de(b_next, b_prev, E_next, E_prev)
        if db_de > 0:
            db_de *= -1
        log_step_info(step, "Backward", b_next, db_de, E_next)

        if E_next < Emin or E_next > Emax or abs(db_de) > slope_max:
            break

        results.append({
            "bscat": b_next,
            "E_rel": E_next,
            "variance": var_next,
            "deck_path": path_next,
            "wse": wse_next
        })

        bscat = b_next
        b_prev = b_next
        E_prev = E_next

    # --- Save and Plot ---
    results_sorted = sorted(results, key=lambda r: r["E_rel"])
    with open("optimized_decks.json", "w") as f:
        json.dump(results_sorted, f, indent=2)

    plt.figure(figsize=(10, 6))
    plt.plot([r['E_rel'] for r in results_sorted], [r['bscat'] for r in results_sorted], marker='o')
    plt.xlabel("E_rel (MeV)")
    plt.ylabel("bscat")
    plt.title("bscat vs E_rel (Forward + Backward Walks)")
    plt.grid(True)
    plt.show()

    return results_sorted

control_file = "he4n_copy.ctrl"
# run_bscat_scan(control_file, 0.0768, 0.01536, 0.25, 0.5, 5.5, 3, -23.8819, 2)
