import yaml
import os
from enum import Enum

rabbit_config = { 'AMQP_URI': "pyamqp://guest:guest@localhost" }

def load_config(filename):
    path = os.path.join(os.path.dirname(__file__), "../config/" + filename)

    with open(path, "r") as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

class DeviceType(Enum):
    HEATER = 1
    PUMP = 2
    SKIMMER = 3
    LIGHT = 4
    TEMP_PROBE = 5

