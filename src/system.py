import os
import shutil
from control import Control

'''
implemented with absolute paths for now
'''

class System:
    def __init__(self, name: str, target_ctrl_file: str, system_ctrl_file: str, three_bp: bool):
        self.name = name
        self.target_ctrl_file = target_ctrl_file
        self.system_ctrl_file = system_ctrl_file
        self.three_bp = three_bp

    def copy_control_files(self):
        current_dir = os.getcwd() # relative to where the script that uses System class is run
        os.chdir(current_dir)
        print(f"Current working directory: {current_dir}")

        # Parent directory of current script (one level up)
        target_dir = current_dir
        print(f"Target copy destination directory: {target_dir}")

        target_copy_path = os.path.join(target_dir, os.path.basename(self.target_ctrl_file))
        system_copy_path = os.path.join(target_dir, os.path.basename(self.system_ctrl_file))

        shutil.copy(self.target_ctrl_file, target_copy_path)
        shutil.copy(self.system_ctrl_file, system_copy_path)

        # Create control objects from copied files
        target_control = Control()
        target_control.read_control(target_copy_path)
        system_control = Control()
        system_control.read_control(system_copy_path)

        # Turn off three-body potential if flag set
        if not self.three_bp:
            target_control.parameters['3b_file'] = 'pots/none.3bp'
            system_control.parameters['3b_file'] = 'pots/none.3bp'

        # Base dir is the parent of the 'ctrl' directory (2 levels above original ctrl file)
        base_dir = os.path.dirname(os.path.dirname(self.target_ctrl_file)) 

        # Convert relative paths in control to absolute paths
        target_control.update_paths(base_dir)
        with open(target_copy_path, 'w') as f:
            target_control.write_control(stream=f.write)
        system_control.update_paths(base_dir)
        with open(system_copy_path, 'w') as f:
            system_control.write_control(stream=f.write)


# system = System("He6", target_ctrl_file="/Users/lydiamazeeva/QMC/nQMCC/nQMCC/ctrl/he6.ctrl", system_ctrl_file="/Users/lydiamazeeva/QMC/nQMCC/nQMCC/ctrl/he6n.ctrl", three_bp=False)
# system.copy_control_files()



