from abc import ABC, abstractmethod
import json
from nameko.web.handlers import http
from nameko.rpc import rpc,RpcProxy
import os
import glob

"""Helper function, for getting all the currently attached DS18B20 sensors"""
def get_DS18B20_sensors():

    """Setup the ds18b20 sensors"""
    os.system('modprobe w1-gpio')
    os.system('modprobe w1-therm')

    base_dir = '/sys/bus/w1/devices/'
    sensor_paths = glob.glob(base_dir + '28*')

    sensor_list = []
    
    index = 1
    for path in sensor_paths:
        sensor = DS18B20("Probe " + str(index), path)
        sensor_list.append(sensor)
        index += 1
    
    return sensor_list

"""Add support for a custom JSON decoding, for my new objects"""
class CustomJSONEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, "__json__"):
            return obj.__json__()
        return json.JSONEncoder.default(self, obj)

class Device(ABC):
    
    def __init__(self, name):
        self.name = name

class TempSensor(Device, ABC):

    @abstractmethod
    def get_temp(self):
        pass

class DS18B20(TempSensor):

    def __init__(self, name, device_path):
        self.device_path = device_path
        super().__init__(name)

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
        

class TempProbeService:
    name = "TempProbeService"

    def __init__(self):
        self.probe_list = get_DS18B20_sensors()

    @rpc
    def list_probes(self):
        return json.dumps(self.probe_list, cls=CustomJSONEncoder)

    @rpc 
    def get_temp(self, index=-1):

        if index >= (len(self.probe_list)):
            return None
        elif index == -1:
            total = 0
            for x in range(len(self.probe_list)):
                temp = self.probe_list[x].get_temp()
                total += temp

            return json.dumps(total/len(self.probe_list))
        else:
            return json.dumps(self.probe_list[index].get_temp())



