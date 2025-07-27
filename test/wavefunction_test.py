import sys
import os
#-----------------------------------------------------------------------
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
#-----------------------------------------------------------------------
from wavefunction import wavefunction_t
#-----------------------------------------------------------------------
if __name__=="__main__":
  wf=wavefunction_t("he4.ctrl","./build/bin/","mpirun -np 4")
  wf.Evaluate("dummy.out")
#-----------------------------------------------------------------------