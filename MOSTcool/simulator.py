from time import sleep
from typing import Optional, Callable
import subprocess
import definitions
from pathlib import Path
import pandas as pd
from datetime import datetime


# Add commands that should be run to this list
commands = [
    ["helics", "run", "--path=runner.json"],
    ["python", "cost_model.py"],
    # Add more as needed
]

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    for line in iter(process.stdout.readline, ''):
        print(line, end='')

    process.wait()
    print(f"Command '{' '.join(command)}' finished with exit code {process.returncode}")

# Function to fix the datetime string and convert it to the correct format
def fix_datetime(dt_str):
    date_part, time_part = dt_str.split()
    # Split the date and time
    # Only adjust if time is '24:00:00', else return the original datetime string
    if time_part == '24:00:00':
        # Convert to datetime object to easily add a day
        dt = pd.to_datetime(date_part, format='%m/%d') + pd.Timedelta(days=1)
        
        # Replace '24:00:00' with '00:00:00' and format the datetime back to string
        # Adjust the format if your date includes the year or other components
        return dt.strftime(' %m/%d') + '  00:00:00'
    else:
        return dt_str

# Prep data: 
# Get X-axis to date time and set it as index
# results = self.results.copy()
def fix_results(results):
    results['Date/Time']= results['Date/Time'].apply(fix_datetime)
    results['Date/Time'] = pd.to_datetime(results['Date/Time'], format='  %m/%d  %H:%M:%S')
    results.set_index('Date/Time', inplace=True)
    return results


class Simulator:
    def __init__(self, idf_path, epw_path, time_step, control_option, datacenter_location):
        self.idf = idf_path
        self.epw = epw_path
        self.ts = time_step
        self.control_option = control_option
        self.datacenter_location = datacenter_location
        self.print_callback: Optional[Callable] = None
        self.sim_starting_callback: Optional[Callable] = None
        self.increment_callback: Optional[Callable] = None
        self.all_done_callback: Optional[Callable] = None
        self.cancel_callback: Optional[Callable] = None

    def add_callbacks(self, print_callback,
                      sim_starting_callback,
                      increment_callback,
                      all_done_callback,
                      cancel_callback):
        self.print_callback = print_callback
        self.sim_starting_callback = sim_starting_callback
        self.increment_callback = increment_callback
        self.all_done_callback = all_done_callback
        self.cancel_callback = cancel_callback
        
    def write_options_to_file(self):
        config_dir = "Output/run_config/"
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        # with open(f"{datetime.now().strftime("%Y/%m/%d %H:%M:%S")}_config.json", "w") as f:
        with open(f"{config_dir}/config.json", "w") as f:
            f.write(f'{{"idf_path": "{self.idf}", "epw_path": "{self.epw}", "time_step": {self.ts}, "control_option": "{self.control_option}", "datacenter_location": "{self.datacenter_location}"}}')

    def run(self) -> None:
        self.print_callback("Hey I am starting")
        sleep(0.5)
        self.sim_starting_callback(len(commands))
        # for i in range(5):
        #     sleep(1)
        #     self.increment_callback(f"Finished with iteration {i}")
        self.write_options_to_file()
        for cmd in commands:
            print(f"Running command: {' '.join(cmd)}")
            run_command(cmd)
            print("-" * 50)  # Separator between command outputs
            self.increment_callback(f"Finished with iteration {commands.index(cmd)}")
        df = pd.read_csv("Output/eplusout.csv")
        self.all_done_callback(fix_results(df))
        
