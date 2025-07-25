import os

class PARAMETERS:
    def __init__(self,file_name_):
        self.FILE_NAME = os.path.splitext(os.path.basename(file_name_))[0]
        print(self.FILE_NAME)
        self.NPART=0
        self.NPROT=0
        self.ISOSPIN_NT=0
        self.NSPART=0
        self.NPPART=0
        self.NSDPART=0
        self.PHI_TYPE=0
        self.NBETA=0
        self.NPHIM=0
        self.NS0=0
        self.MXL=0
        self.MNYOUNG=0
        self.M_SPIN_LIM=0
        self.IMA_LIM=0
        self.NY_LIM=0
        self.KMACO_LIM=0
        self.M_L_LIM=0
        self.NTERM=0
        self.NSTA0=0
        self.NSC0=0
        self.NORTAB_DIM=0
        self.MAX_ICY1=0

    def Read(self):
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]

        if len(lines) != len(self.parameters):
            raise ValueError("Size mismatch between file lines and parameter list.")

        for attr, line in zip(self.parameters, lines):
            setattr(self, attr, line.split()[0])

    def Write(self, stream=None):
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
