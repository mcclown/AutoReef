from nameko.cli.run import run

from common import rabbit_config
from Services.LoggingService import LoggingService
from Services.TempMonitorService import TempMonitorService
from Services.Integrations.TempSensor import DS18B20

services = []
services.append(LoggingService)
services.append(DS18B20)
#services.append(TempMonitorService)

run(services, rabbit_config)
    
