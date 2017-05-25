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

"""Add support for a custom JSON decoding, for my new objects"""
class CustomJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, "__json__"):
            return obj.__json__()
        return json.JSONEncoder.default(self, obj)

class TempSensorState(Enum):

    LOW_TEMP_CRITICAL = 1
    LOW_TEMP_WARNING = 2
    LOW_TEMP = 3
    NORMAL_TEMP = 4
    HIGH_TEMP = 5
    HIGH_TEMP_WARNING = 6
    HIGH_TEMP_CRITICAL = 7


class TempSensor(ABC):

    @abstractmethod
    def get_temp(self):
        pass


class DS18B20(TempSensor):

    device_path = None
    name = None

    def __init__(self, device_path, name=None):
        self.device_path = device_path
        self.name = name

    def __json__(self):
        return {"name" : self.name, "device_path" : self.device_path}
        
    def get_temp(self):
        lines = self.__get_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.get_temp()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            return float(temp_string) / 1000.0

    def __get_temp_raw(self):
        f = open(self.device_path + '/w1_slave', 'r')
        lines = f.readlines()
        f.close()
        return lines

    @classmethod
    def get_all(cls):

        """Setup the ds18b20 sensors"""
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')

        base_dir = '/sys/bus/w1/devices/'
        sensor_paths = glob.glob(base_dir + '28*')

        sensor_list = []
    
        index = 1
        for path in sensor_paths:
            sensor = cls("Probe " + str(index), path)
            sensor_list.append(sensor)
            index += 1
    
        return sensor_list




