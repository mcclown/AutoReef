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
from nameko.events import event_handler

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

    GDOCS_OAUTH_JSON = 'gdocs-config.json' 
    
    # Google Docs spreadsheet name.
    GDOCS_SPREADSHEET_NAME = 'Aquarium Params'

    @event_handler("DS18B20", "high_temp")
    def high_temp_handler(self, payload):
        self.log(payload, "high_temp")        

    @event_handler("DS18B20", "low_temp")
    def low_temp_handler(self, payload):
        self.log(payload, "low_temp")

    @event_handler("DS18B20", "log_temp")
    def norm_temp_handler(self, payload):
        self.log(payload, "log_temp")

    def log(self, payload, message):

        time = payload['time']
        temp = payload['temp']

        print("\nTime:" + time)
        print("Temp:" + str(temp))
        print("State:" + message)
        
        spreadsheet = login_open_sheet(self.GDOCS_OAUTH_JSON, self.GDOCS_SPREADSHEET_NAME)
        spreadsheet.worksheet('WaterTempProbes').append_row((datetime.datetime.strptime(time, "%Y-%m-%d %H:%M:%S.%f"), temp, message))
    
        print('Wrote a row to {0}'.format(self.GDOCS_SPREADSHEET_NAME))

