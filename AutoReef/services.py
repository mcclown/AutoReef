import json
import yaml
import sys
import time
import datetime
import os
import glob
import threading
from enum import Enum
from decimal import *

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from nameko.rpc import rpc
from nameko.events import EventDispatcher, event_handler
from nameko.timer import timer

from AutoReef.integrations import Relay, RelayMode, State, DeviceType, TempSensor, DS18B20
from AutoReef.common import load_config

import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD

"""
    Logging Service 
"""

#Global spreasheet handle and its resource lock
spreadsheet = None
lcd = LCD.Adafruit_CharLCDPlate()
lcd.clear()
lcd.message("Autoreef init...")
lock = threading.RLock()

def login_open_sheet(oauth_key_file, spreadsheet):
    """Connect to Google Docs spreadsheet and return the first worksheet."""

    try:
        scope =  ['https://spreadsheets.google.com/feeds']
        credentials = ServiceAccountCredentials.from_json_keyfile_name(oauth_key_file, scope)
        gc = gspread.authorize(credentials)
        spreadsheet = gc.open(spreadsheet)
        return spreadsheet
    except Exception as ex:
        print('Unable to login and get spreadsheet.  Check OAuth credentials, spreadsheet name, and make sure spreadsheet is shared to the client_email address in the OAuth .json file!')
        print('Google sheet login failed with error:', ex)
        sys.exit(1)


class LoggingService:

    name = "LoggingService"

    print("Init " + name)

    # Google docs details
    GDOCS_OAUTH_JSON = os.path.join(os.path.dirname(__file__), "../config/gdocs-config.json")
    GDOCS_SPREADSHEET_NAME = 'Aquarium Params'
    
    #Start Temp Logging
    @event_handler("TempProbeService", "high_temp_critical")
    def high_temp_critical_handler(self, payload):
        self.log_temp(payload, "high_temp_critical")

    @event_handler("TempProbeService", "high_temp_warning")
    def high_temp_warning_handler(self, payload):
        self.log_temp(payload, "high_temp_warning")

    @event_handler("TempProbeService", "high_temp")
    def high_temp_handler(self, payload):
        self.log_temp(payload, "high_temp")        

    @event_handler("TempProbeService", "low_temp")
    def low_temp_handler(self, payload):
        self.log_temp(payload, "low_temp")

    @event_handler("TempProbeService", "low_temp_warning")
    def low_temp_warning_handler(self, payload):
        self.log_temp(payload, "low_temp_warning")

    @event_handler("TempProbeService", "low_temp_critical")
    def low_temp_critical_handler(self, payload):
        self.log_temp(payload, "low_temp_critical")

    @event_handler("TempProbeService", "log_temp")
    def norm_temp_handler(self, payload):
        self.log_temp(payload, "log_temp")

    #Start Event Logging

    @event_handler("Relay", "event_log")
    def event_log_temp_monitor(self, payload):
        time = str(payload["time"])
        log_level = str(payload["log_level"])
        device_type = str(payload["device_type"])
        name = str(payload["name"])
        message = str(payload["message"])

        global spreadsheet
        
        with lock:
            if spreadsheet == None:
                spreadsheet = login_open_sheet(self.GDOCS_OAUTH_JSON, self.GDOCS_SPREADSHEET_NAME)
        
            try:
                spreadsheet.worksheet('EventLog').append_row((time, name, device_type, message, log_level))
                print("Wrote event log [" + name + "] " + message)
            except Exception as e:
                print("Append error, logging on again")
                print(e)
                spreadsheet = None
                self.event_log_temp_monitor(payload)
    
    def log_temp_lcd(self, state, temp):

        global lcd

        if state == "log_temp":
            #Green
            lcd.set_color(0.0,1.0,0.0) 
            lcd.clear()
            lcd.message("Temp: " + str(temp))
         
        if state.startswith("low"):
            #Blue
            lcd.set_color(0.0,0.0,1.0) 
            lcd.clear()
            lcd.message("Temp: " + str(temp))
        
        if state.startswith("high"):
            #Red
            lcd.set_color(1.0,0.0,0.0) 
            lcd.clear()
            lcd.message("Temp: " + str(temp))
       
    def log_temp(self, payload, message):

        time = payload['time']
        temp = payload['temp']

        print("\nLog Time:" + time)
        print("Log Temp:" + str(temp))
        print("Log State:" + message)
        global spreadsheet
        
        with lock:
            if spreadsheet == None:
                spreadsheet = login_open_sheet(self.GDOCS_OAUTH_JSON, self.GDOCS_SPREADSHEET_NAME)
        
            try:
                
                self.log_temp_lcd(message, temp)
                
                spreadsheet.worksheet('WaterTempProbes').append_row((time, temp, message))
                print("Wrote temp log")
                
            except Exception as e:
                print("Append error, logging on again")
                print(e)
                spreadsheet = None
                self.log_temp(payload, message)       
    

class TempMonitorService:

    name = "TempMonitorService"

    print("Init " + name)

    dispatch = EventDispatcher()

    @event_handler("TempProbeService", "high_temp_warning")
    def high_temp_warning_handler(self, payload):
        print("\nHigh(Warning) temp state reached")

        heaters = Relay.load_by_name("AquaOne 100W")
        for device in heaters:
            if device.state == State.HIGH:
                device.off()

        heaters = Relay.load_by_name("AquaOne 50W")
        for device in heaters:
            if device.state == State.HIGH:
                device.off()


    @event_handler("TempProbeService", "high_temp")
    def high_temp_handler(self, payload):
        print("\nHigh temp state reached")

        heaters = Relay.load_by_name("AquaOne 100W")
        for device in heaters:
            if device.state == State.HIGH:
                device.off()

        heaters = Relay.load_by_name("AquaOne 50W")
        for device in heaters:
            if device.state == State.LOW:
                device.on()



    @event_handler("TempProbeService", "low_temp")
    def low_temp_handler(self, payload):
        print("\nLow temp state reached")

        heaters = Relay.load_by_name("AquaOne 100W")
        for device in heaters:
            if device.state == State.LOW:
                device.on()

        heaters = Relay.load_by_name("AquaOne 50W")
        for device in heaters:
            if device.state == State.HIGH:
                device.off()


    @event_handler("TempProbeService", "low_temp_warning")
    def low_temp_warning_handler(self, payload):
        print("\nLow(Warning) temp state reached")

        heaters = Relay.load_by_name("AquaOne 100W")
        for device in heaters:
            if device.state == State.LOW:
                device.on()

        heaters = Relay.load_by_name("AquaOne 50W")
        for device in heaters:
            if device.state == State.LOW:
                device.on()





class TempProbeService:
    name = "TempProbeService"

    print("Init " + name)


    timer_interval = 60
    dispatch = EventDispatcher()
    config_file="tempProbe1.yaml"

    __conf = None
    __temp_probe = None

    high_temp_critical = None
    high_temp_warning = None
    high_temp = None
    low_temp = None
    low_temp_warning = None
    low_temp_critical = None

    @rpc
    def get_temp(self):

        self.__load_config()
        return self.__temp_probe.get_temp()

    @timer(interval = timer_interval)
    def monitor_temp(self):
        self.__load_config()

        time = datetime.datetime.now()
        temp = self.get_temp()
        state = 'log_temp'
        print("\nProbe Time:" + str(time))
        print("Probe Temp:"+ str(temp))
        

        if temp < self.low_temp_critical:
            state = "low_temp_critical"
        elif self.low_temp_critical <= temp < self.low_temp_warning:
            state = "low_temp_warning"
        elif self.low_temp_warning <= temp < self.low_temp:
            state = 'low_temp'
        elif self.low_temp <= temp < self.high_temp:
            state = 'log_temp'
        elif self.high_temp <= temp < self.high_temp_warning:
            state = 'high_temp'
        elif self.high_temp_warning <= temp < self.high_temp_critical:
            state = 'high_temp_warning'
        else:
            state = 'high_temp_critical'
       
        print("Probe State: " + state)
        self._dispatch_internal(time, temp, state)

    def _dispatch_internal(self, time, temp, state):
        self.dispatch(state, {
            "time": str(time), 
            "temp": temp
            })

    def __load_config(self):

        #Only load config, if it hasn't been already loaded.
        if self.__conf != None:
            return

        self.__conf = load_config(self.config_file)
        
        #Only one type of temp probe, currently. This will have to be made more intelligent, in the future
        self.__temp_probe = DS18B20(self.__conf["device_path"], self.__conf["device_name"])

        self.high_temp_critical = self.__conf["high_temp_critical"] or 99.0
        self.high_temp_warning = self.__conf["high_temp_warning"] or 99.0
        self.high_temp = self.__conf["high_temp"] or 99.0
        self.low_temp = self.__conf["low_temp"] or 0.0
        self.low_temp_warning = self.__conf["low_temp_warning"] or 0.0
        self.low_temp_critical = self.__conf["low_temp_critical"] or 0.0

            


 
