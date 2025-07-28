
"""
wavefunction.py
AutoOpt paths + command line interface
"""
#-----------------------------------------------------------------------
from pathlib import Path
from subprocess import run
import os
import re
#-----------------------------------------------------------------------
from control import control_t
#-----------------------------------------------------------------------
class utility_t:
    FILE_NAME=""
    NQMCC_DIR=""
    BIN_DIR=""
    WORKING_DIR=""
    SYSTEM_TYPE=""
    TARGET_CTRL_FILE=""
    SCATTERING_CTRL_FILE=""
    SYSTEM_FILE=""
    RUN_CMD=[]
#-----------------------------------------------------------------------
    def __init__(self, file_name_):
        self.FILE_NAME = file_name_
        self.Read(self.FILE_NAME)
#-----------------------------------------------------------------------
    def Read(self, filename):
        file = open(self.FILE_NAME.strip("\'"), 'r')
        data = [(l.strip().split()) for l in file.readlines()]
        file.close()
        self.NQMCC_DIR=data[0][0]
        self.BIN_DIR=data[1][0]
        self.WORKING_DIR=data[2][0]
        self.SYSTEM_TYPE=data[3][0]
        self.CTRL_FILE=data[4][0]
#-----------------------------------------------------------------------
        if self.SYSTEM_TYPE.lower() == "sc_scattering":
            self.SCATTERING_CTRL_FILE=data[5][0]
            data=data[6:]
        else:
            data=data[5:]
#-----------------------------------------------------------------------
        self.SYSTEM_FILE=data[0][0]
        self.RUN_CMD=data[1]
#-----------------------------------------------------------------------
def nQMCC(binary: str, ctrl: control_t, bin_dir: str, runner: list, write_log=False, log_name=""):
        cmd = f"{" ".join(runner)} {bin_dir}{binary}".split()
        ctrl.Write(ctrl.FILE_NAME)
        with open(ctrl.FILE_NAME, "r") as ctrl:
            result = run(cmd, stdin=ctrl, capture_output=True, text=True)
        if write_log:
            Path("logs").mkdir(exist_ok=True)
            log_file = Path("logs") / f"{log_name}.{binary}"
            with open(log_file, "a") as f:
                f.write(f"\n===== Command: {' '.join(cmd)} =====\n")
                f.write(result.stdout)
        return result.stdout