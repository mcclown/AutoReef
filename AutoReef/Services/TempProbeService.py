from abc import ABC, abstractmethod
import json
from nameko.rpc import rpc
from nameko.timer import timer
from nameko.events import EventDispatcher
from nameko.dependency_providers import Config
import os
import glob
import datetime
import yaml
from enum import Enum
from AutoReef.common import load_config
from AutoReef.Integrations.TempSensor import TempSensor, DS18B20


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





