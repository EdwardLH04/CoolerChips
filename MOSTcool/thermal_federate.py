import definitions
import helics as h
import logging
import ThermalModel_chip.liddrivencavity as liddrivencavity


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
    federateName = "ThermalFederate"
    
    number_of_days = 365
    total_hours = 24 * number_of_days
    total_seconds = total_hours * 60 * 60
    
    period = total_seconds/2 # 1000
    fed = create_value_federate(fedinitstring, federateName, period)

    federate_name = h.helicsFederateGetName(fed)
    logger.info(f"Created federate {federate_name}")



    PUBS = [
        {
            "Name": "thermal_federate_timestep",
            "Type": "double",
            "Units": "seconds",
            "Global": True,
        }
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
    for i in range(0, len(PUBS)):
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

    time_interval_seconds = int(
        h.helicsFederateGetTimeProperty(fed, h.HELICS_PROPERTY_TIME_PERIOD)
    )
    logger.debug(f"Time interval is {time_interval_seconds} seconds")

    # Blocking call for a time request at simulation time 0
    logger.debug(
        f"Current time is {h.helicsFederateGetCurrentTime(fed)}."
    )
    grantedtime = 0
    logger.debug(f"Granted time {grantedtime}")

    ########## Main co-simulation loop ########################################
    # As long as granted time is in the time range to be simulated...
    while grantedtime < total_seconds:

        # Time request for the next physical interval to be simulated
        requested_time_seconds = grantedtime + time_interval_seconds
        # logger.debug(f"Requesting time {requested_time_seconds}")
        grantedtime = h.helicsFederateRequestTime(fed, requested_time_seconds)
        # logger.debug(f"Granted time {grantedtime} seconds while requested time {requested_time_seconds} seconds with time interval {time_interval_seconds} seconds")
        nth_period = int(grantedtime / time_interval_seconds)
        liddrivencavity.main(nth_period)
        print(f'Running liddrivencavity at {grantedtime}.') #liddrivencavity.main())

        # T_delta_supply = 3 + grantedtime / 1000000000
        h.helicsPublicationPublishDouble(pubid[0], grantedtime)
        # T_delta_return = -1
        # h.helicsPublicationPublishDouble(pubid[1], T_delta_return)
        logger.debug(f"\tPublishing {h.helicsPublicationGetName(pubid[0])} value '{grantedtime}'.")
        # logger.debug(f"\tPublishing {h.helicsPublicationGetName(pubid[1])} value '{T_delta_return}'.")

    # Cleaning up HELICS stuff once we've finished the co-simulation.
    logger.debug(f"Destroying {federateName} federate at time {grantedtime} seconds")
    destroy_federate(fed)
