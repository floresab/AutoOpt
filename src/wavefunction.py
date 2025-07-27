"""
wavefunction.py
nQMCC variational w.f. interface
"""
from pathlib import Path
from subprocess import run
import os
import re
#-----------------------------------------------------------------------
from control import control_t
from parameters import parameters_t
from deck import deck_t
#-----------------------------------------------------------------------
class wavefunction_t:
#-----------------------------------------------------------------------
    def __init__(self,ctrl_file_name,binary_dir_,run_cmd_):
        self.CTRL=control_t(ctrl_file_name)
        self.PARAMS=parameters_t(self.CTRL.INPUT_BRA.PARAM_FILE)
        self.DK=deck_t(self.PARAMS,self.CTRL.INPUT_BRA.DECK_FILE)
        self.OPT=deck_t(self.PARAMS,self.CTRL.OPTIMIZATION_INPUT_FILE)
        self.BINARY_DIR=binary_dir_
        self.RUN_CMD=run_cmd_
#-----------------------------------------------------------------------
    def Evaluate(self,log_name):
        cmd = f"{self.RUN_CMD} {self.BINARY_DIR}energy".split()
        with open(self.CTRL.FILE_NAME, "r") as ctrl:
            result = run(cmd, stdin=ctrl, capture_output=True, text=True)
        Path("logs").mkdir(exist_ok=True)
        log_file = Path("logs") / f"{log_name}.energy"
        with open(log_file, "a") as f:
            f.write(f"\n===== Command: {' '.join(cmd)} =====\n")
            f.write(result.stdout)
            f.write("\n")
        total_average = re.findall(r'H\s*=\s*([-+]?\d+\.\d+)', result.stdout)
        print(total_average)
        energy=0
        var=0
        return energy,var
