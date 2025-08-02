"""
AutoOpt.py
Automatic Optimazation Interface for nQMCC
Quantum Monte Carlo Group @ Washington University in St. Louis
08/01/2025
"""
import sys
import os
import argparse
from datetime import datetime
#-----------------------------------------------------------------------
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
#-----------------------------------------------------------------------
from utility import utility_t
from wavefunction import wavefunction_t,InitPShellScattWF
from bscat import SingleChannelScan
#-----------------------------------------------------------------------
def SingleChannelScattering(util: utility_t):
#-----------------------------------------------------------------------
    BREAK="="*72
#-----------------------------------------------------------------------
    print("SETTING UP WORKING ENVIORMENT")
    try:
        os.mkdir(util.WORKING_DIR)
        os.chdir(util.WORKING_DIR)
    except FileExistsError:
        print("***WORKING DIRECTORY EXISTS***")
        util.WORKING_DIR=f"{util.WORKING_DIR}{util.NAME}-{"_".join(str(datetime.now()).split())}"
        print(f"CURRENT WORKING DIRECTORY: {util.WORKING_DIR}")
        os.mkdir(util.WORKING_DIR)
        os.chdir(util.WORKING_DIR)
#-----------------------------------------------------------------------
    os.mkdir("ctrl")
    os.mkdir("logs")
    os.mkdir("min")
    os.mkdir("opt")
#-----------------------------------------------------------------------
    print("... DONE")
    print(BREAK)
#-----------------------------------------------------------------------
    print("SETTING UP TARGET WAVEFUNCTION")
    target = wavefunction_t(util.CTRL_FILE,util.NQMCC_DIR,util.BIN_DIR,util.RUN_CMD)
    target_label=target.DK.NAME.strip("\'")
    target.CTRL.FILE_NAME=f"{util.WORKING_DIR}target.ctrl"
    target.CTRL.NUM_BLOCKS=util.NUM_BLOCKS
    target.CTRL.BLOCK_SIZE=util.BLOCK_SIZE 
    target.CTRL.WALKERS_PER_NODE=util.WALKERS_PER_NODE
    target.CTRL.NUM_OPT_SAMPLES=util.NUM_OPT_SAMPLES
    print("... DONE")
    print(BREAK)
#-----------------------------------------------------------------------
    for scat_ctrl,ssi in zip(util.SCATTERING_CTRL_FILES,util.SS_INDEXS):
#-----------------------------------------------------------------------
        print("SETTING UP SCATTERING WAVEFUNCTION")
        scatter = wavefunction_t(scat_ctrl,util.NQMCC_DIR,util.BIN_DIR,util.RUN_CMD)
        scatter_label=scatter.DK.NAME.strip("\'")
        scatter.CTRL.FILE_NAME=f"{util.WORKING_DIR}scatter.ctrl"
        scatter.CTRL.NUM_BLOCKS=util.NUM_BLOCKS
        scatter.CTRL.BLOCK_SIZE=util.BLOCK_SIZE 
        scatter.CTRL.WALKERS_PER_NODE=util.WALKERS_PER_NODE
        scatter.CTRL.NUM_OPT_SAMPLES=util.NUM_OPT_SAMPLES
        print("... DONE")
#-----------------------------------------------------------------------
        for const,pot2b,pot3b in zip(util.CONSTANTS_FILES,util.TWO_BODY_FILES,util.THREE_BODY_FILES):
#-----------------------------------------------------------------------
            pot2b_label=pot2b.split(".")[0]
            pot3b_label=pot3b.split(".")[0]
            tname=f"{target_label}.{pot2b_label}.{pot3b_label}"
            sname=f"{scatter_label}.{pot2b_label}.{pot3b_label}"
            print(BREAK)
            print(f"Scanning BSCAT")
            print(f"Target:  {target_label}")
            print(f"Scatter: {scatter_label}")
            print(f"Constants: {const}")
            print(f"V2B: {pot2b}")
            print(f"V3B: {pot3b}")
            target.CTRL.CONST_FILE=f"'{util.NQMCC_DIR}constants/{const}'"
            target.CTRL.L2BP_FILE=f"'{util.NQMCC_DIR}pots/{pot2b}'"
            target.CTRL.L3BP_FILE=f"'{util.NQMCC_DIR}pots/{pot3b}'"
            print(BREAK)
            print(f"EVALUATING TARGET: {target_label}")
            ecore,vcore=target.Evaluate(True,tname)
            print(ecore,vcore)
#-----------------------------------------------------------------------
            scatter.DK.SS[ssi].BSCAT = str(util.INITIAL_BSCAT)
            #Copy Core deck to scatter deck, write deck to file
            InitPShellScattWF(scatter,target,f"{util.WORKING_DIR}temp.dk")
#-----------------------------------------------------------------------
            #SingleChannelScan(util,scatter,ecore,vcore)
#-----------------------------------------------------------------------
def AutoOptAPI(util: utility_t):
#-----------------------------------------------------------------------
    match util.SYSTEM_TYPE.lower():
        case "bound":
            print("todo")
        case "sc_scattering":
            SingleChannelScattering(util)
#-----------------------------------------------------------------------
if __name__ == '__main__':
#-----------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        description="Run AutoOpt using a utility file",
        epilog="""
            Example:
            python3 AutoOpt.py --utility /test/test.util
            """
    )
#-----------------------------------------------------------------------
    parser.add_argument('--utility', required=True, help="/path/to/utility/file")
    args = parser.parse_args()
#-----------------------------------------------------------------------
    util = utility_t(args.utility)
#-----------------------------------------------------------------------
    AutoOptAPI(util)
#-----------------------------------------------------------------------