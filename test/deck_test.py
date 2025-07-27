import sys
import os
#-----------------------------------------------------------------------
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))
#-----------------------------------------------------------------------
from deck import DECK
from parameters import PARAMETERS
#-----------------------------------------------------------------------
if __name__=="__main__":
  params=PARAMETERS("test.params")
  dk=DECK(params,"test.dk")
  dk.Write(params,"dummy.out")
#-----------------------------------------------------------------------