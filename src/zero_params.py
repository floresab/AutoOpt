import os

from deck import Deck, read_params_and_deck

# Function to zero out all float parameters in a deck and its spatial symmetry objects
# If correlation_group is provided, only those params will be set to default value if they are non-zero
def zero_var_params(param_file, deck_file, spatial_sym_name, correlation_groups, default=None):
    deck, deck_name = read_params_and_deck(param_file, deck_file)
    correlation_set = {param for group in correlation_groups for param in group}  # Flattened set for fast lookup

    # Zero all regular float parameters (non-spatial symmetry)
    for key, value in deck.parameters.items():
        if not hasattr(value, '__dict__'):  # regular param
            if isinstance(value, list):
                for i in range(len(value)):
                    if isinstance(value[i], float):
                        value[i] = 0.0
            elif isinstance(value, float):
                deck.parameters[key] = 0.0

    if deck.spatial_symmetries is True:
        for key, sym_obj in deck.parameters.items():
            if hasattr(sym_obj, '__dict__'):
                # spatial symmetry object
                if key == spatial_sym_name:
                    # For input spatial symmetry object, set according to correlation group and non-zero logic
                    for attr_name, attr_value in vars(sym_obj).items():
                        if isinstance(attr_value, float):
                            if attr_name in correlation_set:
                                if attr_value != 0.0:
                                    setattr(sym_obj, attr_name, default * attr_value)
                                else:
                                    setattr(sym_obj, attr_name, 0.0)
                            else:
                                setattr(sym_obj, attr_name, 0.0)
                else:
                    # For other spatial symmetry objects, set all float attributes to zero
                    for attr_name, attr_value in vars(sym_obj).items():
                        if isinstance(attr_value, float):
                            setattr(sym_obj, attr_name, 0.0)

    # save_opt_file(deck, deck_file, base_dir="./opt", wse_flag=(len(correlation_groups) == 1))

    return deck, deck_name


def save_opt_file(bscat, deck, base_dir="./opt", wse_flag=False):
    os.makedirs(base_dir, exist_ok=True)

    deck_base = f"{bscat:.4f}"
    if wse_flag:
        deck_base += "_wse"
    opt_path = os.path.join(base_dir, deck_base)

    deck.write_deck(opt_path, extension="opt")  # specify .opt file

    return opt_path + ".opt"

# zero_var_params('nuclei/params/li7.params', 'nuclei/decks/li7.dk', '4P[21]', [['wse']], default=0.20)
# zero_var_params('nuclei/params/he4n.params', 'nuclei/decks/he5_1hp_av18.dk', '1S[0]', ['spu', 'spv', 'spr', 'spa', 'spb', 'spc', 'spk', 'spl'], default=0.2)
