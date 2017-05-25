#!/usr/bin/env python3

from nameko.cli.run import run

from AutoReef.common import rabbit_config
from AutoReef.Services.LoggingService import LoggingService
from AutoReef.Services.TempMonitorService import TempMonitorService
from AutoReef.Services.Integrations.TempSensor import DS18B20

services = []
services.append(LoggingService)
services.append(DS18B20)
#services.append(TempMonitorService)

run(services, rabbit_config)
    
