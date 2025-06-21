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

    # def copy_control_files(self):
    #     current_dir = os.path.dirname(os.path.abspath(__file__))
    #     os.chdir(current_dir)
    #     print(f"Current working directory: {current_dir}")
    #     # Move two directories up
    #     parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    #     print(f"Parent directory: {parent_dir}")
    #     target_ctrl_path = os.path.join(parent_dir, "ctrl", self.target_ctrl_file)
    #     system_ctrl_path = os.path.join(parent_dir, "ctrl", self.system_ctrl_file)
    #     print(f"Control directory: {target_ctrl_path}")
    #     print(f"System control file: {system_ctrl_path}")

    #     # copy control files to working directory
    #     shutil.copy(target_ctrl_path, self.target_ctrl_file)
    #     shutil.copy(system_ctrl_path, self.system_ctrl_file)

    #     # create control objects
    #     target_control = Control()
    #     target_control.read_control(self.target_ctrl_file)
    #     system_control = Control()
    #     system_control.read_control(self.system_ctrl_file)

    #     # turn off three-body potential if flag set
    #     if not self.three_bp:
    #         target_control.parameters['3b_file'] = 'pots/none.3bp'
    #         system_control.parameters['3b_file'] = 'pots/none.3bp'

    #     # change relative paths to absolute paths in the control files
    #     target_control.update_paths(parent_dir)
    #     target_control.write_control()
    #     system_control.update_paths(parent_dir)
    #     system_control.write_control()

    def copy_control_files(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(current_dir)
        print(f"Current working directory: {current_dir}")

        # Parent directory of current script (one level up)
        target_dir = os.path.dirname(current_dir)
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


system = System("He6", target_ctrl_file="/Users/lydiamazeeva/QMC/nQMCC/nQMCC/ctrl/he6.ctrl", system_ctrl_file="/Users/lydiamazeeva/QMC/nQMCC/nQMCC/ctrl/he6n.ctrl", three_bp=False)
system.copy_control_files()



