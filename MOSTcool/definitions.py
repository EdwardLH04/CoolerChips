import os
from pathlib import Path
from enum import IntEnum
import json

# Available control options
class CONTROL_OPTIONS(IntEnum):
    CHANGE_LIQUID_COOLING = 1
    CHANGE_SUPPLY_DELTA_T = 2
    CHANGE_IT_LOAD = 3
    
# TODO: select a control option

if os.path.exists('Output/run_config/config.json'):
    with open('Output/run_config/config.json', 'r') as f:
        data = json.load(f)
        control_option_name = data["control_option"]
        try:
            CONTROL_OPTION = CONTROL_OPTIONS[control_option_name]
        except KeyError:
            print(f"Invalid control option: '{control_option_name}'. Using default CONTROL_OPTION value as CHANGE_IT_LOAD")
            CONTROL_OPTION = CONTROL_OPTIONS.CHANGE_IT_LOAD
else:   
    print("No config file found. Using default CONTROL_OPTION value as CHANGE_IT_LOAD")
    CONTROL_OPTION = CONTROL_OPTIONS.CHANGE_IT_LOAD
    
if CONTROL_OPTION == CONTROL_OPTIONS.CHANGE_LIQUID_COOLING:
    IDF_PATH = "Resources/energyplus_files/2ZoneDataCenterCRAHandplant.idf"
else:
    IDF_PATH = "Resources/energyplus_files/2ZoneDataCenterCRAHandplant_aircoolingonly.idf"

OUTPUT_DIR = "./Output"
ENERGYPLUS_INSTALL_PATH = "../EnergyPlus"
LOCATION_MAP = {
    "Chicago, IL" : "USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
    "San Francisco, CA" : "USA_CA_San.Francisco.Intl.AP.724940_TMY3.epw",
    "Dulles Airport, VA" : "USA_VA_Sterling-Washington.Dulles.Intl.AP.724030_TMY3.epw",
    "Tampa, FL": "USA_FL_Tampa.Intl.AP.722110_TMY3.epw"
}

if os.path.exists('Output/run_config/config.json'):
    with open('Output/run_config/config.json', 'r') as f:
        data = json.load(f)
        datacenter_location_name = data["datacenter_location"]
        EPW_FILE = LOCATION_MAP[datacenter_location_name]
        EPW_PATH = os.path.join(ENERGYPLUS_INSTALL_PATH, "WeatherData", EPW_FILE)
else:   
    print("No config file found. Using default EPW_PATH value as USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")
    EPW_PATH = os.path.join(ENERGYPLUS_INSTALL_PATH, "WeatherData/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw")


RESOURCES_DIR = "./Resources"
GRAPHS_DIR = os.path.join(OUTPUT_DIR, "graphs")
Path(GRAPHS_DIR).mkdir(parents=True, exist_ok=True)

TIMESTEP_PERIOD_SECONDS = 600  # 10 mins
NUMBER_OF_DAYS = 14   # Two weeks
TOTAL_SECONDS = 60 * 60 * 24 * NUMBER_OF_DAYS

ACTUATORS = [
    {
        "component_type": "Schedule:Compact",
        "control_type": "Schedule Value",
        "actuator_key": "Load Profile 1 Load Schedule",
        "actuator_unit": "1"
    },
    {
        "component_type": "Schedule:Constant",
        "control_type": "Schedule Value",
        "actuator_key": "Supply Temperature Difference Schedule Mod",   # delta T at supply side
        "actuator_unit": "C"
    },
    {
        "component_type": "Schedule:Constant",
        "control_type": "Schedule Value",
        "actuator_key": "Return Temperature Difference Schedule Mod",   # delta T at return side
        "actuator_unit": "C"
    },
    {
        "component_type": "Schedule:Compact",
        "control_type": "Schedule Value",
        "actuator_key": "Data Center CPU Loading Schedule",
        "actuator_unit": "1"
    },
    {
        "component_type": "Schedule:Compact",
        "control_type": "Schedule Value",
        "actuator_key": "Load Profile 1 Flow Frac Schedule",
        "actuator_unit": "1"
    }
]

# old, for testing
# ACTUATORS = [
#     {
#         "component_type": "Schedule:Constant",
#         "control_type": "Schedule Value",
#         "actuator_key": "Supply Temperature Difference Schedule Mod",
#         "actuator_unit": "C"
#     },
#     {
#         "component_type": "Schedule:Constant",
#         "control_type": "Schedule Value",
#         "actuator_key": "Return Temperature Difference Schedule Mod",
#         "actuator_unit": "C"
#     }
# ]


SENSORS = [
    {
        "variable_name": "Facility Total HVAC Electricity Demand Rate",
        "variable_key": "Whole Building",
        "variable_unit": "W"
    },
    {
        "variable_name": "Facility Total Electricity Demand Rate",
        "variable_key": "Whole Building",
        "variable_unit": "W"
    },
    # EASTDATACENTER_EQUIP:ITE Standard Density Air Volume Flow Rate [m3/s](TimeStep)
    {
        "variable_name": "Fan Air Mass Flow Rate",
        "variable_key": "East Zone Supply Fan",
        "variable_unit": "m3/s"
    },
    {
        "variable_name": "System Node Temperature",
        "variable_key": "East Air Loop Outlet Node",
        "variable_unit": "C"
    }
]


LOG_LEVEL_MAP = { # Maps the log level string to helics Integer log level
    # more info: https://docs.helics.org/en/helics2/user-guide/logging.html
    "helics_log_level_no_print": -1,
    "helics_log_level_error": 0,
    "helics_log_level_warning": 1,
    "helics_log_level_summary": 2,
    "helics_log_level_connections": 3,
    "helics_log_level_interfaces": 4,
    "helics_log_level_timing": 5,
    "helics_log_level_data": 6,
    "helics_log_level_trace": 7,
}

