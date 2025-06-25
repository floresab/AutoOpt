import os
import shutil
from control import Control

'''
implemented with absolute paths
'''

class System:
    def __init__(self, name: str, target_ctrl_file: str, scattering_ctrl_file: str, three_bp: bool, E_start: float): 
        self.name = name
        self.target_ctrl_file = os.path.basename(target_ctrl_file) # just the file name, not the full path
        self.scattering_ctrl_file = os.path.basename(scattering_ctrl_file)
        self.three_bp = three_bp
        self.E_start = E_start  # MeV, energy to start optimization from
        self.target_control, self.scattering_control = self.copy_control_files(target_ctrl_file, scattering_ctrl_file)
        self.potentials = ['AV18'] # default potential for he4n, can be overridden later
        self.channels = ['1/2+'] # default channel for he4n, can be overridden later
    


    def copy_control_files(self, target_ctrl_file, scattering_ctrl_file):
        current_dir = os.getcwd() # relative to where the script that uses System class is run
        os.chdir(current_dir)
        print(f"Current working directory: {current_dir}")

        # Parent directory of current script (one level up)
        target_dir = current_dir
        print(f"Target copy destination directory: {target_dir}")

        target_copy_path = os.path.join(target_dir, os.path.basename(target_ctrl_file))
        scattering_copy_path = os.path.join(target_dir, os.path.basename(scattering_ctrl_file))

        shutil.copy(target_ctrl_file, target_copy_path)
        shutil.copy(scattering_ctrl_file, scattering_copy_path)

        # Create control objects from copied files
        target_control = Control()
        target_control.read_control(target_copy_path)
        scattering_control = Control()
        scattering_control.read_control(scattering_copy_path)

        # Turn off three-body potential if flag set
        if not self.three_bp:
            target_control.parameters['3b_file'] = 'pots/none.3bp'
            scattering_control.parameters['3b_file'] = 'pots/none.3bp'

        # Base dir is the parent of the 'ctrl' directory (2 levels above original ctrl file)
        base_dir = os.path.dirname(os.path.dirname(target_ctrl_file)) 

        # Convert relative paths in control to absolute paths
        target_control.update_paths(base_dir)
        target_control.write_control()
        scattering_control.update_paths(base_dir)
        scattering_control.write_control()

        return target_control, scattering_control

        


# system = System("He6", target_ctrl_file="/Users/lydiamazeeva/QMC/nQMCC/nQMCC/ctrl/he6.ctrl", system_ctrl_file="/Users/lydiamazeeva/QMC/nQMCC/nQMCC/ctrl/he6n.ctrl", three_bp=False, E_start=3.0)
# print(system.system_ctrl_file)



