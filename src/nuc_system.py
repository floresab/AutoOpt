
class NuclearSystem:
    def __init__(self, system_file):
        self.parameters = {}
        self.read_system(system_file)

    def __getitem__(self, key):
        return self.parameters[key]

    def __setitem__(self, key, value):
        self.parameters[key] = value

    def read_system(self, filename):

        self.system_file = filename 

        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        for line in lines:
            tokens = line.split()
            key = tokens[-1].lower()
            values = tokens[:-1]

            if key in {"2b_potentials", "3b_potentials", "channels"}:
                self.parameters[key] = [str(v) for v in values]
            elif key in {"e_start", "e_min", "e_max", "input_de", "input_db"}:
                self.parameters[key] = float(values[0])
            elif key in {"name", "spatial_symmetry"}:
                self.parameters[key] = values[0]
            else:
                raise ValueError(f"Unknown key in system file: {key}")

    def write_system(self, filename=None):

        filename = self.system_file

        with open(filename, 'w') as f:
            for key, value in self.parameters.items():
                if isinstance(value, list):
                    line = " ".join(str(v) for v in value)
                elif isinstance(value, float):
                    line = f"{value:.6f}"
                else:
                    line = str(value)
                f.write(f"{line:<40} {key}\n")

