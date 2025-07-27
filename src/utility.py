
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
        self.WORKING_DIR=da ta[2][0]
        self.SYSTEM_TYPE=data[3][0]
        self.CTRL_FILE=data[4][0]
#-----------------------------------------------------------------------
        if self.SYSTEM_TYPE.tolower() == "scattering":
            self.SCATTERING_CTRL_FILE=data[5][0]
            data=data[6:]
        else:
            data=data[5:]
#-----------------------------------------------------------------------
        self.SYSTEM_FILE=data[0][0]
        self.RUN_CMD=data[1]
#-----------------------------------------------------------------------


