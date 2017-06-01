import json
import yaml
import sys
import time
import datetime
import os
import glob
import threading
from enum import Enum

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

    # Google docs details
    GDOCS_OAUTH_JSON = os.path.join(os.path.dirname(__file__), "../config/gdocs-config.json")
    GDOCS_SPREADSHEET_NAME = 'Aquarium Params'
    
    #Start Temp Logging

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
            except:
                print("Append error, logging on again")
                spreadsheet = None
                self.event_log_temp_monitor(payload)
    
    def log_temp_lcd(self, state, temp):

        global lcd

        if state == "log_temp":
            #Green
            lcd.set_color(0.0,1.0,0.0) 
            lcd.clear()
            lcd.message("Temp: " + str(temp))
         
        if state == "low_temp":
            #Blue
            lcd.set_color(0.0,0.0,1.0) 
            lcd.clear()
            lcd.message("Temp: " + str(temp))
        
        if state == "high_temp":
            #Red
            lcd.set_color(1.0,0.0,0.0) 
            lcd.clear()
            lcd.message("Temp: " + str(temp))
       
    def log_temp(self, payload, message):

        time = payload['time']
        temp = payload['temp']

        print("\nTime:" + time)
        print("Temp:" + str(temp))
        print("State:" + message)
        global spreadsheet
        
        with lock:
            if spreadsheet == None:
                spreadsheet = login_open_sheet(self.GDOCS_OAUTH_JSON, self.GDOCS_SPREADSHEET_NAME)
        
            try:
                
                self.log_temp_lcd(message, temp)
                
                spreadsheet.worksheet('WaterTempProbes').append_row((time, temp, message))
                print("Wrote temp log")
                
            except:
                print("Append error, logging on again")
                spreadsheet = None
                self.log_temp(payload, message)       
    

class TempMonitorService:

    name = "TempMonitorService"
    dispatch = EventDispatcher()

    @event_handler("DS18B20", "high_temp_warning")
    def high_temp_warning_handler(self, payload):
        pass

    @event_handler("DS18B20", "high_temp")
    def high_temp_handler(self, payload):
        print("High temp state reached")

        heaters = Relay.load_by_name("AquaOne 100W")
        for device in heaters:
            if device.state == State.HIGH:
                device.off()

        heaters = Relay.load_by_name("AquaOne 50W")
        for device in heaters:
            if device.state == State.LOW:
                device.on()



    @event_handler("DS18B20", "low_temp")
    def low_temp_handler(self, payload):
        print("Low temp state reached")

        heaters = Relay.load_by_name("AquaOne 100W")
        for device in heaters:
            if device.state == State.LOW:
                device.on()

        heaters = Relay.load_by_name("AquaOne 50W")
        for device in heaters:
            if device.state == State.HIGH:
                device.off()

    @event_handler("DS18B20", "low_temp_warning")
    def low_temp_warning_handler(self, payload):
        pass




class TempProbeService:
    name = "TempProbeService"

    'Abstract class for all different types of temperature sensors'

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

        print("\nTime:" + str(time))
        print("Temp:"+ str(temp))

        if self.high_temp != None and temp > self.high_temp:
            state = "high_temp"
        elif self.low_temp != None and temp < self.low_temp:
            state = "low_temp"

        self._dispatch_internal(time, temp, state)

    def _dispatch_internal(self, time, temp, state):
        print("State:" + state)
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

        self.high_temp_critical = self.__conf["high_temp_critical"]
        self.high_temo_warning = self.__conf["high_temp_warning"]
        self.high_temp = self.__conf["high_temp"]
        self.low_temp = self.__conf["low_temp"]
        self.low_temp_warning = self.__conf["low_temp_warning"]
        self.low_temp_critical = self.__conf["low_temp_critical"]





