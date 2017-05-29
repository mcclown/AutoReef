#!/usr/bin/env python3

from nameko.cli.run import run

from AutoReef.common import rabbit_config
from AutoReef.services import LoggingService, TempMonitorService, TempProbeService

services = []
services.append(LoggingService)
#services.append(TempMonitorService)
services.append(TempProbeService)

run(services, rabbit_config)
    
