import definitions
import helics as h
import logging


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


def create_value_federate(fedinitstring, name, period):
    """Create a value federate with the given name and time period."""

    fedinfo = h.helicsCreateFederateInfo()
    h.helicsFederateInfoSetCoreTypeFromString(
        fedinfo, "zmq"
    )  # ZMQ is the default and works well for small co-simulations
    h.helicsFederateInfoSetCoreInitString(
        fedinfo, fedinitstring
    )  # Can be used to set number of federates, etc
    h.helicsFederateInfoSetIntegerProperty(fedinfo, h.HELICS_PROPERTY_INT_LOG_LEVEL, definitions.LOG_LEVEL_MAP["helics_log_level_warning"])
    h.helicsFederateInfoSetTimeProperty(fedinfo, h.HELICS_PROPERTY_TIME_PERIOD, period)
    h.helicsFederateInfoSetFlagOption(
        fedinfo, h.HELICS_FLAG_UNINTERRUPTIBLE, True
    )  # Forces the granted time to be the requested time (i.e., EnergyPlus timestep)
    h.helicsFederateInfoSetFlagOption(
        fedinfo, h.HELICS_FLAG_TERMINATE_ON_ERROR, True
    )  # Stop the whole co-simulation if there is an error
    h.helicsFederateInfoSetFlagOption(
        fedinfo, h.HELICS_FLAG_WAIT_FOR_CURRENT_TIME_UPDATE, False
    )  # This makes sure that this federate will be the last one granted a given time step. Thus it will have the most up-to-date values for all other federates.
    fed = h.helicsCreateValueFederate(name, fedinfo)
    return fed


def destroy_federate(fed):
    """Cleaning up HELICS stuff once we've finished the co-simulation."""
    h.helicsFederateDestroy(fed)
    logger.info("Federate finalized")


if __name__ == "__main__":

    ##############  Registering  federate  ##########################
    fedinitstring = " --federates=1"
    name = "Controller"
    period = definitions.TIMESTEP_PERIOD_SECONDS
    fed = create_value_federate(fedinitstring, name, period)

    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")

    PUBS = [
        {
            "Name": f'{actuator["component_type"]}/{actuator["control_type"]}/{actuator["actuator_key"]}',
            "Type": "double",
            "Units": actuator["actuator_unit"],
            "Global": True,
        }
        for actuator in definitions.ACTUATORS
    ]

    SUBS = [
        {
            "Name": sensor["variable_key"] + "/" + sensor["variable_name"],
            "Type": "double",
            "Units": sensor["variable_unit"],
            "Global": True,
        }
        for sensor in definitions.SENSORS
    ]

    pubid = {}
    pubs_without_1 = list(range(0, len(PUBS)))
    pubs_without_1.remove(1)  # 1 is with server federate now. 
    for i in pubs_without_1:
        pubid[i] = h.helicsFederateRegisterGlobalTypePublication(
            fed, PUBS[i]["Name"], PUBS[i]["Type"], PUBS[i]["Units"]
        )
        pub_name = h.helicsPublicationGetName(pubid[i])
        logger.debug(f"\tRegistered publication---> {pub_name}")

    subid = {}
    for i in range(0, len(SUBS)):
        subid[i] = h.helicsFederateRegisterSubscription(
            fed, SUBS[i]["Name"], SUBS[i]["Units"]
        )
        sub_name = h.helicsInputGetTarget(subid[i])
        logger.debug(f"\tRegistered subscription---> {sub_name}")

    sub_count = h.helicsFederateGetInputCount(fed)
    logger.debug(f"\tNumber of subscriptions: {sub_count}")
    pub_count = h.helicsFederateGetPublicationCount(fed)
    logger.debug(f"\tNumber of publications: {pub_count}")

    ##############  Entering Execution Mode  ##################################
    h.helicsFederateEnterExecutingMode(fed)
    logger.info("Entered HELICS execution mode")

    # TODO: need to extract runperiod info from E+ model
    full_day_seconds = 24 * 3600
    # time_interval_seconds = 10  # get this from IDF timestep?
    time_interval_seconds = int(
        h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD)
    )
    logger.debug(f"Time interval is {time_interval_seconds} seconds")

    # Blocking call for a time request at simulation time 0
    logger.debug(
        f"Current time is {h.helicsFederateGetCurrentTime(fed)}."
    )
    grantedtime = 0
    liquid_load = 0
    logger.debug(f"Granted time {grantedtime}")


    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < definitions.TOTAL_SECONDS:

        # Time request for the next physical interval to be simulated
        requested_time_seconds = grantedtime + time_interval_seconds
        # logger.debug(f"Requesting time {requested_time_seconds}")
        grantedtime = h.helicsFederateRequestTime(fed, requested_time_seconds)
        # logger.debug(f"Granted time {grantedtime} seconds while requested time {requested_time_seconds} seconds with time interval {time_interval_seconds} seconds")
        num_of_hours_in_day = grantedtime % full_day_seconds / 3600.0

        # use one of the options below, comment out the other options
        # Option1: change liquid cooling load
        # create 24/7 schedule
        if definitions.CONTROL_OPTION == definitions.CONTROL_OPTIONS.CHANGE_LIQUID_COOLING:
            if num_of_hours_in_day < 6.0:    # 0:00-6:00
                liquid_load = -200000.0
            elif num_of_hours_in_day < 12.0:
                liquid_load = -400000.0
            elif num_of_hours_in_day < 18.0:
                liquid_load = -800000.0
            elif num_of_hours_in_day < 24.0:
                liquid_load = -1200000.0
            h.helicsPublicationPublishDouble(pubid[0], liquid_load)
            # h.helicsPublicationPublishDouble(pubid[1], 2.0)  # supply approach always 2C
            h.helicsPublicationPublishDouble(pubid[2], 1.0)  # CPU load schedule always 1, major load as liquid cooling
            h.helicsPublicationPublishDouble(pubid[3], 1)  # Liquid load flow rate fraction. This can be updated realtime according to the dynamic load
            h.helicsPublicationPublishDouble(pubid[4], 0)  # Load Profile 1 Flow Frac = 0
            # TODO: need to update the peak flow rate of E+ object "LoadProfile:Plant" according to the maximum liquid cooling load input.
            # this is for design purposes, to correctly sizing the cooling system, including chiller, pumps, and cooling tower
            # see energyPlusAPI_Example.py

        # Option2: change supply approach temperature
        if definitions.CONTROL_OPTION == definitions.CONTROL_OPTIONS.CHANGE_SUPPLY_DELTA_T:
            T_delta_supply = 2 + grantedtime / 500000
            h.helicsPublicationPublishDouble(pubid[0], 0)  # liquid load as 0
            # h.helicsPublicationPublishDouble(pubid[1], T_delta_supply)
            h.helicsPublicationPublishDouble(pubid[2], 1.0)  # CPU load schedule always 1
            h.helicsPublicationPublishDouble(pubid[3], 0)  # Liquid load flow rate fraction = 0, i.e., no liquid cooling
            h.helicsPublicationPublishDouble(pubid[4], 0)  # Load Profile 1 Flow Frac = 0

        # Option3: change IT server load
        if definitions.CONTROL_OPTION == definitions.CONTROL_OPTIONS.CHANGE_IT_LOAD:
            it_load_frac = 1 - grantedtime / definitions.TOTAL_SECONDS
            h.helicsPublicationPublishDouble(pubid[0], 0)  # liquid load as 0
            # h.helicsPublicationPublishDouble(pubid[1], 2)
            h.helicsPublicationPublishDouble(pubid[2], it_load_frac)  # CPU load schedule fraction
            h.helicsPublicationPublishDouble(pubid[3], 0)  # Liquid load flow rate fraction = 0, i.e., no liquid cooling
            h.helicsPublicationPublishDouble(pubid[4], 0)  # Load Profile 1 Flow Frac = 0

        # T_delta_supply = 2 + grantedtime / 10000000
        # h.helicsPublicationPublishDouble(pubid[0], T_delta_supply)
        # T_delta_return = -1
        # h.helicsPublicationPublishDouble(pubid[1], T_delta_return)
        # logger.debug(f"\tPublishing {h.helicsPublicationGetName(pubid[0])} value '{T_delta_supply}'.")
        # logger.debug(f"\tPublishing {h.helicsPublicationGetName(pubid[1])} value '{T_delta_return}'.")

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    logger.debug(f"Destroying federate at time {grantedtime} seconds")
    destroy_federate(fed)
