from enum import Enum

from nameko.events import event_handler
from nameko.rpc import rpc
from nameko.dependency_providers import Config

import RPi.GPIO as GPIO

class GPIODevice:

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

    def __init__(self, pin, direction):
        self.pin = pin
        self.direction = direction
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, self.direction)

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW)

class RelayMode(Enum):
    NORMAL_OPEN = 1
    NORMAL_CLOSED = 2

class State(Enum):
    HIGH = 1
    LOW = 0
    ERROR = 2

class Relay(GPIODevice):

    relay_mode = RelayMode.NORMAL_OPEN

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

    def __init__(self, pin, direction, relay_mode):
        
        if self.direction == GPIO.IN:
            """Relays can't be input, so throw an exception if it's been configured that way"""
            pass

        self.relay_mode = relay_mode
        super().__init__(pin, direction)

    def on(self):
        if self.relay_mode == RelayMode.NORMAL_OPEN:
            super().on()
        else:
            super().off()
        
    def off(self):
        if self.relay_mode == RelayMode.NORMAL_OPEN:
            super().off()
        else:
            super().on()




