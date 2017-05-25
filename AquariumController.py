#!/usr/bin/env python3

import argparse
import datetime
import os
from AutoReef.Services.Integrations.HardwareControl import Relay, State, DeviceType

parser = argparse.ArgumentParser()
parser.add_argument("-t", "--heater", action="store_true")
parser.add_argument("-p", "--pump", action="store_true")
parser.add_argument("-s", "--skimmer", action="store_true")
parser.add_argument("-l", "--lights", action="store_true")
parser.add_argument("--init", action="store_true")
parser.add_argument("desired_state", help="on|off", nargs="?")
parser.add_argument("device_name", default=None, nargs="?")
args = parser.parse_args()


if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")

def manage_relay_by_type(device_type, desired_state):
    
    relays = Relay.load_by_type(device_type)

    for x in relays:
        if desired_state == "on":
            x.on()
        else:
            x.off()

def manage_relay_by_name(device_name, desired_state):

    relays = Relay.load_by_name(device_name)

    for x in relays:
        if desired_state == "on":
            x.on()
        else:
            x.off()

if args.device_name != None:

    manage_relay_by_name(args.device_name, args.desired_state)

if args.heater:
    manage_relay_by_type(DeviceType.HEATER, args.desired_state)

if args.pump:
    manage_relay_by_type(DeviceType.PUMP, args.desired_state)

if args.skimmer:
    manage_relay_by_type(DeviceType.SKIMMER, args.desired_state)

if args.lights:
    manage_relay_by_type(DeviceType.LIGHT, args.desired_state)

if args.init:
    hour = datetime.datetime.now().hour

    """Check if lights should be on"""
    if hour >= 9 and hour < 21:
        manage_relay_by_name("2 x PL-18W", "on")
    else:
        manage_relay_by_name("Refugium LED", "on")

