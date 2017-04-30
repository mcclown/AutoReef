from enum import Enum

from nameko.events import event_handler
from nameko.rpc import rpc
from nameko.dependency_providers import Config

import RPi.GPIO as GPIO

class GPIODevice:

    pin = None
    direction = None
    
    state = None

    def __init__(self, pin, direction):
        self.pin = pin
        self.direction = direction
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, self.direction)

        if self.direction == GPIO.OUT:
            GPIO.output(self.pin, GPIO.LOW)
            self.state = GPIO.LOW

    def on(self):
        if self.direction == GPIO.IN:
            """Throw exception here"""
            pass

        GPIO.output(self.pin, GPIO.HIGH)
        self.state = GPIO.HIGH

    def off(self):
        if self.direction ==  GPIO.IN:
            """throw exception here"""
            pass

        GPIO.output(self.pin, GPIO.LOW)
        self.state = GPIO.LOW

    def read(self):
        if self.direction == GPIO.OUT:
            """throw exception"""
            pass
        
        self.state = None
        return GPIO.input(self.pin)

class RelayMode(Enum):
    NORMAL_OPEN = 1
    NORMAL_CLOSED = 2

class RelayState(Enum):
    ON = 1
    OFF = 2

class Relay(GPIODevice):

    relay_mode = RelayMode.NORMAL_OPEN

    def __init__(self, pin, direction, relay_mode):
        
        if self.direction == GPIO.IN:
            """Relays can't be input, so throw an exception if it's been configured that way"""
            pass

        self.relay_mode = relay_mode
        super().__init__(pin, direction)

        if relay_mode == RelayMode.NORMAL_OPEN:
            self.state = RelayState.OFF
        else:
            self.state = RelayState.ON

    def on(self):
        if self.relay_mode == RelayMode.NORMAL_OPEN:
            super().on()
        else:
            super().off()
        
        self.state = RelayState.ON

    def off(self):
        if self.relay_mode == RelayMode.NORMAL_OPEN:
            super().off()
        else:
            super().on()

        self.state = RelayState.OFF



