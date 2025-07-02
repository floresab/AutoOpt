from abc import ABC, abstractmethod
import os

# This module defines the WavefunctionInput class and its subclasses for reading and writing wavefunction input files.

# The WavefunctionInput class is an abstract base class that provides a framework for handling wavefunction input parameters.
class WavefunctionInput(ABC):

    def __init__(self):

        self.attributes = []
        self.attribute_groups = [] # list of lists for related parameters
    
    # helper functions to set parameters
    def set_attr(self, key, value):
        setattr(self, key, value)
        self.attributes.append(key)
        self.attribute_groups.append([key])

    def set_group(self, tokens):
        n = len(tokens)
        half = n // 2
        values = tokens[:half]
        keys = tokens[half:]

        if len(values) != len(keys):
            raise ValueError("Mismatch between values and keys")

        for i, (val, key) in enumerate(zip(values, keys)):
            value = int(val) if i == 0 else val
            setattr(self, key, value)
            self.attributes.append(key)
        self.attribute_groups.append(keys)

    # helper function to read parameter groups
    def read_standard_groups(self, lines, start_line, num_lines):
        for j in range(start_line, start_line + num_lines):
            tokens = lines[j].strip().split()
            self.set_group(tokens)
        return start_line + num_lines

    # method to write output
    def write_output(self, stream=None):
        if stream is None:
            stream = print
        for group in self.attribute_groups:
            values = []
            labels = []
            for param in group:
                val = getattr(self, param)
                values.append(str(val))
                labels.append(param)
            values_str = "  ".join(values)
            label_str = "  ".join(labels)
            spacing = max(80, len(values_str) + 2)
            line = f"{values_str:<{spacing}}{label_str}"
            stream(line.rstrip() + "\n")

    @abstractmethod
    def read_wavefunction_input(self, input_lines, start_line):
        pass

    def resolve_paths(self, base_dir):
        for attr in dir(self):
            val = getattr(self, attr, None)
            if isinstance(val, str):
                stripped = val.strip("'\"")
                full_path = os.path.join(base_dir, stripped)
                setattr(self, attr, f"'{full_path}'")


# subclass of WavefunctionInput for reading and writing variational wavefunction input files
class VariationalWavefunctionInput(WavefunctionInput):

    def __init__(self):
        super().__init__()

    def read_wavefunction_input(self, lines, start_line):
        i = start_line
        self.set_attr('param_file', lines[i].strip().split()[0]); i += 1
        self.set_attr('deck_file', lines[i].strip().split()[0]); i += 1
        end_line = self.read_standard_groups(lines, i, 3)
        return end_line
        
    
# subclass of WavefunctionInput for reading and writing product wavefunction input files
class ProductWavefunctionInput(WavefunctionInput):
    def __init__(self):
        super().__init__()
    
    def read_wavefunction_input(self, lines, start_line):
        i = start_line
        self.set_attr('product_param_file', lines[i].strip().split()[0]); i += 1
        self.set_attr('product_deck_file', lines[i].strip().split()[0]); i += 1
        self.set_attr('param_file', lines[i].strip().split()[0]); i += 1
        self.set_attr('deck_file', lines[i].strip().split()[0]); i += 1
        end_line = self.read_standard_groups(lines, i, 3)
        return end_line

# subclass of WavefunctionInput for reading and writing deuteron wavefunction input files    
class DeuteronWavefunctionInput(WavefunctionInput):
    def __init__(self):
        super().__init__()
    
    def read_wavefunction_input(self, lines, start_line): # no blocks to read for deuteron wavefunction
        return start_line
    


    
            
    