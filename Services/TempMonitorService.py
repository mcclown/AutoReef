#!/usr/bin/python

import json
import sys
import time
import datetime
import os
import glob

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from nameko.rpc import rpc
from nameko.events import event_handler, EventDispatcher

from Integrations.HardwareControl import Relay, RelayMode, State, DeviceType
import RPi.GPIO as GPIO


class TempMonitorService:

    name = "TempMonitorService"
    dispatch = EventDispatcher()

    @event_handler("DS18B20", "high_temp_warning")
    def high_temp_warning_handler(self, payload):
        pass

    @event_handler("DS18B20", "high_temp")
    def high_temp_handler(self, payload):
        heaters = Relay.load_by_type(DeviceType.HEATER)
        
        for device in heaters:
            if device.state == State.HIGH:
                device.off()


    @event_handler("DS18B20", "low_temp")
    def low_temp_handler(self, payload):
        heaters = Relay.load_by_type(DeviceType.HEATER)
        
        for device in heaters:
            if device.state == State.LOW:
                device.on()

    @event_handler("DS18B20", "low_temp_warning")
    def low_temp_warning_handler(self, payload):
        pass


