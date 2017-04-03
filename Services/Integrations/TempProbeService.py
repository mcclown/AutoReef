import json
from nameko.web.handlers import http
import os
import glob

"""Setup the ds18b20 sensors"""
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

base_dir = '/sys/bus/w1/devices/'
ds_sensorList = glob.glob(base_dir + '28*')

def read_dstemp_raw(ds_sensor):
    f = open(ds_sensor, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_dstemp():
    tempList = []

    for ds_sensor in ds_sensorList:
        lines = read_dstemp_raw(ds_sensor+'/w1_slave')
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp = float(temp_string) / 1000.0
            tempList.append(temp)
    
    return tempList

class TempProbeService:
    name = "TempProbeService"

    @http('GET', '/listProbes')
    def get_method(self, request):
        return json.dumps(ds_sensorList)

    @http('GET', '/getTemp')
    def do_post(self, request):
        return json.dumps(read_dstemp())


