import os

class Parameters:
    def __init__(self):

        self.name = ""
        self.parameters = [
            'NPART', 'NPROT', 'ISOSPIN_NT', 'NSPART', 'NPPART', 'NSDPART',
            'PHI_TYPE', 'NBETA', 'NPHIM', 'ns0', 'mxl', 'mnyoung', 'm_spin_lim',
            'ima_lim', 'ny_lim', 'kmaco_lim', 'm_l_lim', 'nterm', 'nsta0',
            'nsc0', 'nortab_dim', 'max_icy1'
        ]

        for attr in self.parameters:
            setattr(self, attr, 0)

    def read_parameters(self, filename):

        self.name = os.path.splitext(os.path.basename(filename))[0]

        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        if len(lines) != len(self.parameters):
            raise ValueError("Size mismatch between file lines and parameter list.")

        for attr, line in zip(self.parameters, lines):
            setattr(self, attr, line.split()[0])

    def write_parameters(self, stream=None):
        if stream is None:
            filename = f"{self.name}.params" # write in-place
            with open(filename, 'w') as f:
                for attr in self.parameters:
                    value = getattr(self, attr)
                    f.write(f"{value:<8} {attr}\n")
        else:
            for attr in self.parameters:
                value = getattr(self, attr)
                print(f"{value:<8} {attr}\n")

# param = Parameters()
# param.read_parameters('nuclei/params/he4n.params')
# param.write_parameters(stream = print)