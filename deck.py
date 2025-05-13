from spatial_symmetry import read_spatial_symmetries
from parameters import Parameters
import os

class Deck:

    int_values = {
        'PI', 'lwf', 'lsc', 'lopc', 'lcut',
        'lfsp0', 'e_or_v', 'lscat', 'lmu1', 'Lmu2', 'LL', 'lnodes'
    }

    arrays = {
        'esep': 4,
        'eta': 2, 'zeta': 2,
        'fscal': 8, 'ac': 8, 'aa': 8, 'ar': 8, 'alpha': 8, 'beta': 8, 'gamma': 8
    }
    
    def __init__(self):
        self.Name = ""
        self.parameters = []
        self.parameter_groups = [] # list of lists for related parameters
        
        # Initialize arrays
        for attr, size in self.arrays.items():
            setattr(self, attr, [0.0 for i in range(size)])
    
    # helper functions
    def parse_group(self, group, tokens):
        for param, value in zip(group, tokens):
            parsed = int(value) if param in self.int_values else float(value)
            setattr(self, param, parsed)
        self.parameters.extend(group)
  
    def set_array_from_line(self, tokens, array_name):
        array = getattr(self, array_name)
        for i in range(len(array)):
            array[i] = float(tokens[i])
        self.parameters.append(array_name)
        self.parameter_groups.append([array_name])

    def set_param(self, tokens):
        values = tokens[:len(tokens) // 2]
        param_names = tokens[len(tokens) // 2:]
        self.parse_group(param_names, values)
        self.parameter_groups.append(param_names)
      


    def read_deck(self, filepath, parameters):

        with open(filepath, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
            self.Name = lines[0].rsplit(' ', 1)[0].strip()            # Extract name from first line
            self.parameter_groups.append(['Name'])

        for i in range(1,19):                                         # Logic always the same for the first 18 lines
            tokens = lines[i].strip().split()
            if tokens[-1] in self.arrays:
                self.set_array_from_line(tokens, tokens[-1])
            else:
                self.set_param(tokens)
        
        # Logic changes at this line based on .params file
        current_line = 19

        NPPART = int(parameters.NPPART)
        NDPART = int(parameters.NSDPART)

        nppart_lines = min(NPPART, 3)                   # max 3 correlation lines (spu, ppu, etc.)
        ndpart_lines = sum([3, 2, 1][:min(NDPART, 3)])  # up to 6 lines total for sd/pp/dd correlation
        extra_lines = nppart_lines + ndpart_lines

        for i in range(current_line, current_line + extra_lines):
            tokens = lines[i].strip().split()
            self.set_param(tokens)
        
        # Read the spatial symmetries
        if (NPPART != 0):
            self.spatial_symmetries = read_spatial_symmetries(
                lines, current_line + extra_lines,
                nbeta=int(parameters.NBETA),
                nppart=NPPART,
                ndpart=NDPART,
                phi_type=int(parameters.PHI_TYPE)
            )

    
    def write_deck(self, filename):
        filename = f"{filename}_.dk"
        with open(filename, 'w') as f:
            for group in self.parameter_groups:
                values = []
                labels = []

                for param in group:
                    val = getattr(self, param)
                    if isinstance(val, list):
                        values.extend(f"{x:.5f}" for x in val)
                        labels.append(param)
                    else:
                        values.append(f"{val:<8}")
                        labels.append(param)

                # Format values into a string
                values_str = " ".join(values)

                label_str = " ".join(labels)
                spacing = max(80, len(values_str) + 2)  # ensure room for labels
                line = f"{values_str:<{spacing}}{label_str}"
                f.write(line.rstrip() + "\n")
            if hasattr(self, 'spatial_symmetries'):
                for ss in self.spatial_symmetries:
                    for group in ss.correlation_groups:
                        values = [getattr(ss, name) for name in group]
                        line = format_group_line(values)
                        comment = "  " + " ".join(group)
                        f.write(f"{line:<80}{comment}\n")
            
# Helper function to format group lines
def format_group_line(values):
    formatted = []
    for val in values:
        if isinstance(val, float):
            formatted.append(f"{val:>8.5f}")
        elif isinstance(val, int):
            formatted.append(f"{val:>4d}")
        elif isinstance(val, str):
            formatted.append(f"{val:<10}")
        else:
            formatted.append(str(val))
    return " ".join(formatted)

# Helper function to read the deck and parameters
def read_deck_and_params(param_file, deck_file):
    params = Parameters()
    params.read_parameters(param_file)

    deck = Deck()
    deck.read_deck(deck_file, params)

    deck_name = os.path.splitext(os.path.basename(param_file))[0]

    return deck, deck_name


deck, deck_name = read_deck_and_params('li6n.params', 'li6n_1hp.dk')
deck.write_deck(deck_name)
# deck = read_deck_and_params('be7.params', 'be7.dk')
# deck, deck_name = read_deck_and_params('h3.params', 'h3_.dk')
    





