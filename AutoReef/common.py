import yaml
import os

rabbit_config = { 'AMQP_URI': "pyamqp://guest:guest@localhost" }

def load_config(filename):
    path = os.path.join(os.path.dirname(__file__), "../config/" + filename)

    with open(path, "r") as stream:
        try:
            return yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)

