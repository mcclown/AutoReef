#!/usr/bin/env python3

import argparse
import datetime
import os
import RPi.GPIO as GPIO
from Services.Integrations.HardwareControl import Relay, RelayMode

HEATER1_PIN=20
HEATER2_PIN=21
PUMP_PIN=22
SKIMMER_PIN=23
LIGHT_PIN=25

parser = argparse.ArgumentParser()
parser.add_argument("-h1", "--heater1", action="store_true")
parser.add_argument("-h2", "--heater2", action="store_true")
parser.add_argument("-p", "--pump", action="store_true")
parser.add_argument("-s", "--skimmer", action="store_true")
parser.add_argument("-l", "--lights", action="store_true")
parser.add_argument("--init", action="store_true")
parser.add_argument("desired_state", help="on|off")
args = parser.parse_args()

if os.geteuid() != 0:
    exit("You need to have root privileges to run this script.\nPlease try again, this time using 'sudo'. Exiting.")


if args.heater1:
    device = Relay(HEATER1_PIN, RelayMode.NORMAL_CLOSED)
    if args.desired_state == "on":
        device.on()
    else:
        device.off()

if args.heater2:
    device = Relay(HEATER2_PIN, RelayMode.NORMAL_CLOSED)
    if args.desired_state == "on":
        device.on()
    else:
        device.off()

if args.pump:
    device = Relay(PUMP_PIN, RelayMode.NORMAL_CLOSED)
    if args.desired_state == "on":
        device.on()
    else:
        device.off()

if args.skimmer:
    device = Relay(SKIMMER_PIN, RelayMode.NORMAL_CLOSED)
    if args.desired_state == "on":
        device.on()
    else:
        device.off()

if args.lights:
    device = Relay(LIGHT_PIN, RelayMode.NORMAL_OPEN)
    if args.desired_state == "on":
        device.on()
    else:
        device.off()

if args.init:
    hour = datetime.datetime.now().hour

    """Check if lights should be on"""
    if hour >= 9 and hour < 21:
       device = Relay(LIGHT_PIN, RelayMode.NORMAL_OPEN)
       device.on()

