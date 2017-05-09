from enum import Enum
import yaml
import os
import time

from nameko.events import event_handler, EventDispatcher
from nameko.rpc import rpc

import RPi.GPIO as GPIO


class RelayMode(Enum):
    NORMAL_OPEN = 1
    NORMAL_CLOSED = 2


class State(Enum):
    HIGH = 1
    LOW = 0
    ERROR = 2


class DeviceType(Enum):
    HEATER = 1
    PUMP = 2
    SKIMMER = 3
    LIGHT = 4

class LogLevel:
    DEBUG = 1
    INFO = 2
    WARN = 3
    CRIT = 4
    ERROR = 5

class GPIODevice:
    
    device_name = None
    pin = None
    direction = None
    
    @property
    def state(self):
        val = GPIO.input(self.pin)

        if val == 0:
            return State.LOW
        elif val == 1:
            return State.HIGH
        else:
            return State.ERROR

    def __init__(self, pin, direction, name = None):
        self.name = name
        self.pin = pin
        self.direction = direction

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, self.direction)

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW)


class Relay(GPIODevice):
    
    name = "Relay"
    dispatch = EventDispatcher()

    relay_mode = RelayMode.NORMAL_OPEN
    device_type = None

    @property
    def state(self):
        val = GPIO.input(self.pin)

        if val == 0 and self.relay_mode == RelayMode.NORMAL_OPEN:
            return State.LOW
        elif val == 1 and self.relay_mode == RelayMode.NORMAL_OPEN:
            return State.HIGH
        elif val == 0 and self.relay_mode == RelayMode.NORMAL_CLOSED:
            return State.HIGH
        elif val == 1 and self.relay_mode == RelayMode.NORMAL_CLOSED:
            return State.LOW
        else:
            return State.ERROR

    def __init__(self, pin, relay_mode, device_type = None, name = None):
        self.relay_mode = relay_mode
        self.device_type = device_type

        super().__init__(pin, GPIO.OUT, name)

    def on(self):
        try:
            if self.relay_mode == RelayMode.NORMAL_OPEN:
                super().on()
            else:
                super().off()

            self._log(LogLevel.INFO, "Turned on")
        except:
            self._log(LogLevel.ERROR, "Unable to turn on")
        
    def off(self):
        try:
            if self.relay_mode == RelayMode.NORMAL_OPEN:
                super().off()
            else:
                super().on()

            self._log(LogLevel.INFO, "Turned off")
        except:
            self._log(LogLevel.ERROR, "Unable to turn off")

    def _log(self, log_level, message):
        time = datetime.datetime.now()
        
        self.dispatch("event_log", {
            "time" : str(time),
            "log_level" : str(log_level),
            "device_type" : str(self.device_type),
            "name" : self.device_name,
            "message" : message
            })

    @classmethod
    def load_by_name(cls, name):
        config = cls._load_config()
        matches = [x for x in config if x["name"] == name]

        return cls._config_to_obj(matches)

    @classmethod
    def load_by_type(cls, device_type):
        config = cls._load_config()
        matches = [x for x in config if ("DeviceType." + x["device_type"]) == str(device_type)]

        return cls._config_to_obj(matches)

    @classmethod
    def _load_config(cls):
        path = os.path.join(os.path.dirname(__file__), "../../config/relayConfig.yaml")

        with open(path, "r") as stream:
            try:
                return yaml.load(stream)
            except yaml.YAMLError as exc:
                print(exc)

    @classmethod
    def _config_to_obj(cls, conf_list):
        relay_list = []    
        
        for conf in conf_list:
            name = conf["name"]
            device_type = getattr(DeviceType, conf["device_type"], None)
            pin = conf["pin"]
            relay_mode = getattr(RelayMode, conf["relay_mode"], None)

            relay = cls(pin, relay_mode, device_type, name)
            relay_list.append(relay)
        
        return relay_list

