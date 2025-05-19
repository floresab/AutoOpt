import os

from wavefunction_input import WavefunctionInput, VariationalWavefunctionInput, ProductWavefunctionInput, DeuteronWavefunctionInput

# This class is used to group control parameters together
class ControlGroup:
    def __init__(self, owner, param_names):
        self.owner = owner
        self.param_names = param_names

    def write_output(self, stream=None):
        if stream is None:
            stream = print
        values = []
        labels = []
        for param in self.param_names:
            val = getattr(self.owner, param)
            values.append(str(val))
            labels.append(param)
        values_str = "  ".join(values)
        label_str = "  ".join(labels)
        spacing = max(80, len(values_str) + 2)
        line = f"{values_str:<{spacing}}{label_str}"
        stream(line.rstrip() + "\n")

# This class is used to read and write the control file
class Control:

    int_values = {
        'read_write_walk', 
        'ke', 'lemp',
        'num_blocks', 'block_size',
        'burn_in', 'num_moves_between',
        'npts', 'one_over_dx', 'fd_factor',
        'lastp_sample_type',
        'reg_flag',
        'stop_after_group',
        'nlopt_method',  'num_opt_walks',  'num_opt_evaluations'
    }

    strings = {
        'basis', 'walk_file', 'constants_file', '2b_file', '3b_file', 'group_file', 'nortab_file', 'optimization_input', 'optimized_deck', 'scratch_dir'
    }

    boolean_values = {
        'bra_eq_ket', 'sample_L2'
    }


    def __init__(self):
        self.Name = ""
        self.sections = [] # stores ControlGroup or WavefunctionInput objects

    # helper functions
    def parse_group(self, group, tokens):
        for key, value in zip(group, tokens):
            if key in self.int_values:
                parsed = int(value)
            elif key in self.strings:
                parsed = str(value)
            elif key in self.boolean_values:
                val = value.strip().lower()
                parsed = val
            else:
                parsed = float(value)
            setattr(self, key, parsed)

    def set_param(self, tokens):
        if len(tokens) % 2 != 0:            
            tokens.append('blank')                # pad with a blank string for consistency ('ance reg_flag gam e1 v1 e2 v2' line has 8 values but 7 param names)
        values = tokens[:len(tokens) // 2]        # first half are values
        keys = tokens[len(tokens) // 2:]          # second half are parameter names
        self.parse_group(keys, values)
        self.sections.append(ControlGroup(self, keys))


    def read_control(self, control_file):
        with open(control_file, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
            self.Name = os.path.splitext(os.path.basename(control_file))[0]

        # Phase 1: Read initial control lines
        index = 0
        for _ in range(2):                                         
            tokens = lines[index].split()
            self.set_param(tokens)
            index += 1

        # Phase 2: Handle wavefunction(s)
        def read_wavefunction_block(start_line, label='wf_type'):
            wf_type = lines[start_line].split()[0]
            setattr(self, label, wf_type)
            self.sections.append(ControlGroup(self, [label]))

            wf = create_wavefunction_input(wf_type)
            self.sections.append(wf)
            end_line = wf.read_wavefunction_input(lines, start_line + 1)
            return end_line

        if getattr(self, 'bra_eq_ket') == '.false.':  # if bra and ket are different, two wavefunction blocks
            index = read_wavefunction_block(index, label='ket_wf_type')
            index = read_wavefunction_block(index, label='bra_wf_type')
        else:
            index = read_wavefunction_block(index, label='wf_type')

        # Phase 3: Read the rest of control parameters
        while index < len(lines):
            tokens = lines[index].split()
            self.set_param(tokens)
            index += 1

    
    def write_control(self, stream=None):
        if stream is None:
            filename = f"{self.Name}_.ctrl"
            with open(filename, 'w') as f:
                for section in self.sections:
                    section.write_output(stream=f.write)
        else:
            for section in self.sections:
                section.write_output(stream=stream)


# helper function to create wavefunction input based on type
def create_wavefunction_input(wf_type: str) -> WavefunctionInput:
    if wf_type == "'variational'":
        return VariationalWavefunctionInput()
    elif wf_type == "'product'":
        return ProductWavefunctionInput()
    elif wf_type == "'deuteron'":
        return DeuteronWavefunctionInput()
    else:
        raise ValueError(f"Unknown wavefunction type: {wf_type}")
    

control = Control()
control.read_control('he4n_spec.ctrl')
# control.read_control('d.ctrl')
control.write_control(stream=print)
