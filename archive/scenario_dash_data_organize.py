import shutil
import os
import argparse
import utilities as utils

dash_config = utils.load_config('config/dashboard.yaml')
SCENARIO_root = dash_config['scenario_files_root']

class ScenarioFilesDumper:
    def __init__(self, source_dir, destination_dir):
        self.source_dir = source_dir
        self.destination_dir = destination_dir

    def dump(self):
        # source_results_dir = os.path.join(self.source_dir, 'results')
        destination_results_dir = os.path.join(SCENARIO_root, self.destination_dir)
        shutil.copytree(self.source_dir, destination_results_dir, dirs_exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description='Dump files from source directory to destination directory')
    parser.add_argument('source_dir', type=str, help='Path to the source directory')
    parser.add_argument('destination_dir', type=str, help='Path to the destination directory')
    args = parser.parse_args()
    
    scenario_dumper = ScenarioFilesDumper(args.source_dir, args.destination_dir)
    scenario_dumper.dump()

if __name__ == '__main__':
    main()
