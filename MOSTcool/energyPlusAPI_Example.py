"""An example for how to use the EnergyPlus Python API with HELICS."""
from dataclasses import dataclass
import os
from pathlib import Path
import federate as federate
import definitions
import sys


# We specify the path to the EnergyPlus installation directory
ENERGYPLUS_INSTALL_PATH = definitions.ENERGYPLUS_INSTALL_PATH
# Add the path to the pyenergyplus directory to sys.path
sys.path.append(ENERGYPLUS_INSTALL_PATH)
from pyenergyplus.api import EnergyPlusAPI


@dataclass
class Actuator:
    component_type: str
    control_type: str
    actuator_key: str
    sub_instance: federate.Sub = None  # The current value of the acuator is stored here
    actuator_handle: str = None


@dataclass
class Sensor:
    variable_name: str
    variable_key: str
    variable_unit: str = None
    pub_instance: federate.Pub = None  # The current value of the sensor is stored here
    sensor_handle: str = None


# Define a dictionary to store the results - unnecessary if you don't need it. 
results = {"HVAC Energy": [], "Total Energy": [], "Time": [], "Liquid Cooling Load": [], "Supply Approach Temperature": [], "CPU load": []}


class energyplus_runner:
    def __init__(self, output_dir, epw_path, idf_path):
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        self.epw_path = epw_path
        self.idf_path = idf_path
        self.api = EnergyPlusAPI()
        self.warmup_done = False
        self.warmup_count = 0
        self.actuators = [
            Actuator(
                component_type=actuator["component_type"],
                control_type=actuator["control_type"],
                actuator_key=actuator["actuator_key"],
                sub_instance=federate.Sub(name=f'{actuator["component_type"]}/{actuator["control_type"]}/{actuator["actuator_key"]}', unit=actuator["actuator_unit"])
            )
            for actuator in definitions.ACTUATORS
        ]
        self.sensors = [
            Sensor(
                variable_name=sensor["variable_name"],
                variable_key=sensor["variable_key"],
                variable_unit=sensor["variable_unit"],
                pub_instance=federate.Pub(name=f'{sensor["variable_key"]}/{sensor["variable_name"]}', unit=sensor["variable_unit"])
            )
            for sensor in definitions.SENSORS
        ]
        
        self.ep_federate = federate.mostcool_federate(federate_name="EnergyPlus", 
                                                      subscriptions=[Actuator.sub_instance for Actuator in self.actuators], 
                                                      publications=[Sensor.pub_instance for Sensor in self.sensors])
        

    def set_actuators(self, state):
        for actuator in self.actuators:
            handle = self.api.exchange.get_actuator_handle(
                state,
                actuator.component_type,
                actuator.control_type,
                actuator.actuator_key,
            )
            self.api.exchange.set_actuator_value(
                state, handle, actuator.sub_instance.value
            )

    def get_sensors(self, state):
        for sensor in self.sensors:
            handle = self.api.exchange.get_variable_handle(
                state, sensor.variable_name, sensor.variable_key
            )
            sensor.pub_instance.value = self.api.exchange.get_variable_value(
                state, handle
            )


    def _warmup_complete_callback(self, state):
        # There are multiple warmup periods in this IDF, so we need to go through this
        print(f"Warmup {self.warmup_count+1} complete!")
        self.warmup_count = self.warmup_count + 1
        if self.warmup_count > 2:
            self.warmup_done = True


    def _timestep_callback(self, state):
        if self.warmup_done:

            # Request next time
            self.ep_federate.request_time()

            # Get subbed actuator values and set them in EnergyPlus
            subs = self.ep_federate.update_subs()
            for sub in subs:
                if sub.name == "Schedule:Compact/Schedule Value/Load Profile 1 Load Schedule":
                    results["Liquid Cooling Load"].append(sub.value*(-1))
                elif sub.name == "Schedule:Constant/Schedule Value/Supply Temperature Difference Schedule Mod":
                    results["Supply Approach Temperature"].append(sub.value)
                elif sub.name == "Schedule:Compact/Schedule Value/Data Center CPU Loading Schedule":
                    results["CPU load"].append(sub.value)
            
            self.set_actuators(state)

            # Get sensor values from EnergyPlus and publish them
            self.get_sensors(state)
            self.ep_federate.update_pubs()
            for pub in self.ep_federate.pubs:
                sensor_name = pub.name
                sensor_value = pub.value
                if sensor_name == "Whole Building/Facility Total HVAC Electricity Demand Rate":
                    results["HVAC Energy"].append(sensor_value)
                elif sensor_name == "Whole Building/Facility Total Electricity Demand Rate":
                    results["Total Energy"].append(sensor_value)
            results["Time"].append(self.ep_federate.granted_time)

    def run(self):
        state = self.api.state_manager.new_state()
        # Register callbacks
        # TODO: add line below to update idf setting to reflect data center design customization if any
        # self.api.runtime.callback_after_component_get_input(state, self._before_sizing_callback)
        # e.g., liquid cooling design flow rate (current peak design uses 1m3/s as placeholder, can update through
        # actuator called "Plant Load Profile" with control type called "Mass Flow Rate" (in kg/s)

        self.api.runtime.callback_after_new_environment_warmup_complete(
        state, self._warmup_complete_callback
        )
        self.api.runtime.callback_end_zone_timestep_after_zone_reporting(
            state, self._timestep_callback
        )
        # Run EnergyPlus
        exit_code = self.api.runtime.run_energyplus(
            state,
            [
                "-r",
                "-d",
                self.output_dir,
                "-w",
                self.epw_path,
                self.idf_path,
            ],
        )
        print(f"EnergyPlus exited with code: {exit_code}, at HELICS time {self.ep_federate.granted_time}.")
        self.ep_federate.destroy_federate()


energyplus_runner = energyplus_runner(
    definitions.OUTPUT_DIR, definitions.EPW_PATH, definitions.IDF_PATH
)
energyplus_runner.run()

# plot ep_fed.results["Time"] vs ep_fed.results["Energy"]
import matplotlib.pyplot as plt

# time_slice = slice(31392, 32400)  # this is August 1-7 in annual simulation
if definitions.CONTROL_OPTION == definitions.CONTROL_OPTIONS.CHANGE_LIQUID_COOLING:
    time_slice = slice(4464, 5472)  # this is August 1-7 in Jul-Aug runperiod
    y2 = results["Liquid Cooling Load"][time_slice]
    y2_label = "Liquid Cooling Load (W)"
elif definitions.CONTROL_OPTION == definitions.CONTROL_OPTIONS.CHANGE_SUPPLY_DELTA_T:
    time_slice = slice(None)  # this is whole Jul to Aug
    y2 = results["Supply Approach Temperature"][time_slice]
    y2_label = "Supply Approach Temperature (C)"
elif definitions.CONTROL_OPTION == definitions.CONTROL_OPTIONS.CHANGE_IT_LOAD:
    time_slice = slice(None)  # this is whole Jul to Aug
    y2 = results["CPU load"][time_slice]
    y2_label = "CPU load fraction"
else:
    print("CONTROL_OPTION not defined correctly in definitions.py")
x = results["Time"][time_slice]
y1 = results["HVAC Energy"][time_slice]

fig, ax1 = plt.subplots()
ax1.plot(x, y1, 'g-')
ax1.set_xlabel('Time (s)')
ax1.set_ylabel('HVAC Energy (W)', color='g')
# Plot the second data set on the secondary axis
ax2 = ax1.twinx()
ax2.plot(x, y2, 'b--')  # Blue solid line
ax2.set_ylabel(y2_label, color='b')
if definitions.CONTROL_OPTION == definitions.CONTROL_OPTIONS.CHANGE_LIQUID_COOLING:
    ax2.set_ylim([0, 2000000])  # for CHANGE_LIQUID_COOLING only


# plt.show()
plt.savefig((os.path.join(definitions.OUTPUT_DIR, "graphs", f"OutputImage_{definitions.CONTROL_OPTION}.pdf")), format="pdf", bbox_inches="tight")
