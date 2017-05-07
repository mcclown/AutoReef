#!/usr/bin/python

import json
import sys
import time
import datetime
import os
import glob
import threading

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from nameko.rpc import rpc
from nameko.events import event_handler

#Global spreasheet handle and its resource lock
spreadsheet = None
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
    GDOCS_OAUTH_JSON = 'gdocs-config.json' 
    GDOCS_SPREADSHEET_NAME = 'Aquarium Params'
    
    #Start Temp Logging

    @event_handler("DS18B20", "high_temp_warning")
    def high_temp_warning_handler(self, payload):
        self.log_temp(payload, "high_temp_warning")

    @event_handler("DS18B20", "high_temp")
    def high_temp_handler(self, payload):
        self.log_temp(payload, "high_temp")        

    @event_handler("DS18B20", "low_temp")
    def low_temp_handler(self, payload):
        self.log_temp(payload, "low_temp")

    @event_handler("DS18B20", "low_temp_warning")
    def low_temp_warning_handler(self, payload):
        self.log_temp(payload, "low_temp_warning")

    @event_handler("DS18B20", "log_temp")
    def norm_temp_handler(self, payload):
        self.log_temp(payload, "log_temp")

    #Start Event Logging

    @event_handler("TempMonitorService", "event_log")
    def event_log_temp_monitor(self, payload):
        time = payload["time"]
        device_type = payload["device_type"]
        name = payload["name"]
        message = payload["message"]
        
        global spreadsheet
        
        with lock:
            if spreadsheet == None:
                spreadsheet = login_open_sheet(self.GDOCS_OAUTH_JSON, self.GDOCS_SPREADSHEET_NAME)
        
            try:
                spreadsheet.worksheet('EventLog').append_row((time, name, device_type, message))
                print("Wrote event log [" + name + "] " + message)
            except:
                print("Append error, logging on again")
                spreadsheet = None
                self.event_log_temp_monitor(payload)

        
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
                spreadsheet.worksheet('WaterTempProbes').append_row((time, temp, message))
                print("Wrote temp log")
            except:
                print("Append error, logging on again")
                spreadsheet = None
                self.log_temp(payload, message)

       
    


