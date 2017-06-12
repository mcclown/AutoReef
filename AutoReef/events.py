from enum import Enum
import pickle

import datetime

from AutoReef.common import DeviceType

class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARN = 3
    CRIT = 4
    ERROR = 5

class Event:

    def __init__(self, source, name, device_type=None):
        self.time = datetime.datetime.now()
        self.source = source
        self.name = name

        if device_type != None and not isinstance(device_type, DeviceType):
            raise TypeError("'device_type', if defined, must be of type 'DeviceType'")

        self.device_type = device_type

        self.__data = None
    
    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, data):
        
        if not isinstance(data, EventData):
            raise TypeError("'data' must be of type 'EventData'")

        self.__data = data


    def pickle(self):
        return pickle.dumps(self)
        
    @classmethod
    def depickle(cls, pickled_event):
        return pickle.loads(pickled_event)


class EventData:

    def __init__(self, value, unit):
        self.value = value
        self.unit = unit

    
class EventQueue:
    _event_list = []
    
    def add_event(self):
        pass


