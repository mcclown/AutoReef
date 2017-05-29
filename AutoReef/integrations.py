from enum import Enum
import yaml
import os
import datetime
import glob
import time
import threading
from abc import ABC, abstractmethod
import json

from nameko.rpc import rpc
from nameko.timer import timer
from nameko.events import EventDispatcher, event_handler
from nameko.dependency_providers import Config
from nameko.standalone.events import event_dispatcher
from nameko.events import event_handler

from AutoReef.common import rabbit_config, load_config

import RPi.GPIO as GPIO
import Adafruit_CharLCD as LCD

"""
Relays / GPIO
"""

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

#TODO: Really need to move this somewhere else
class LogLevel(Enum):
    DEBUG = 1
    INFO = 2
    WARN = 3
    CRIT = 4
    ERROR = 5

class GPIODevice:
    
    name = None
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
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, self.direction)

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW)


class Relay(GPIODevice):
    
    relay_mode = RelayMode.NORMAL_OPEN
    device_type = None
    config_file="relayConfig.yaml"

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
        if self.state != State.HIGH:
            try:
                if self.relay_mode == RelayMode.NORMAL_OPEN:
                    super().on()
                else:
                    super().off()

                self._log(LogLevel.INFO, "Turned on")
            except:
                self._log(LogLevel.ERROR, "Unable to turn on")
        
    def off(self):
        if self.state != State.LOW:
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

        payload = {
            "time" : str(time),
            "log_level" : str(log_level),
            "device_type" : str(self.device_type),
            "name" : self.name,
            "message" : message
            }

        dispatch = event_dispatcher(rabbit_config)

        dispatch("Relay", "event_log", payload)

    @classmethod
    def load_all(cls):
        config = load_config(cls.config_file)
        return cls._config_to_obj(config)

    @classmethod
    def load_by_name(cls, name):
        config = load_config(cls.config_file)
        matches = [x for x in config if x["name"] == name]

        return cls._config_to_obj(matches)

    @classmethod
    def load_by_type(cls, device_type):
        config = load_config(cls.config_file)
        matches = [x for x in config if ("DeviceType." + x["device_type"]) == str(device_type)]

        return cls._config_to_obj(matches)

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

"""
LCD Panel / Controller
"""

# Initialize the LCD using the pins
lock = threading.RLock()

# Show some basic colors.
#RED lcd.set_color(1.0, 0.0, 0.0)
#GREEN lcd.set_color(0.0, 1.0, 0.0)
#BLUE lcd.set_color(0.0, 0.0, 1.0)
#YELLOW lcd.set_color(1.0, 1.0, 0.0)
#CYAN lcd.set_color(0.0, 1.0, 1.0)
#MAGENTA lcd.set_color(1.0, 0.0, 1.0)
#WHITE lcd.set_color(1.0, 1.0, 1.0)


class EventQueue:
    
    _event_list = []

    def add_event(self):
        pass


class LCDController(EventQueue):

    _lcd = None
    _event_mode=True

    def __init__(self):
        self.reset()

    def reset(self):
        self._lcd = LCD.Adafruit_CharLCDPlate()
        self._lcd.clear()
        self._lcd.message("AutoReef init...")

    
    def check_button_thread(self):

        while True:
            # Loop through each button and check if it is pressed.
            for button in buttons:
                try:
                    if lcd.is_pressed(button[0]):
                        

                        # Button is pressed, change the message and backlight.
                        lcd.clear()
                        lcd.message(button[1])
                        lcd.set_color(button[2][0], button[2][1], button[2][2])
                except OSError:
                    print("OSError")

    def display_event_thread(self):
        pass

class EventListener:
    name="EventListener"

    @event_handler("DS18B20", "log_temp")
    def temp_event_handler(self, payload):
        lcd.add_event(payload)
        

    @event_handler("Relay", "event_log")
    def relay_event_handler(self, payload):
        lcd.add_event(payload)



"""
    Temp Sensors
"""


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


