#!/usr/bin/env python3

from nameko.cli.run import run

from AutoReef.common import rabbit_config
from AutoReef.services import LoggingService, TempMonitorService, TempProbeService

print("Start services")
services = []
services.append(LoggingService)
print("- logging")
services.append(TempMonitorService)
print("- tempmon")
services.append(TempProbeService)
print("- tempprobe")

print("running...\n")
run(services, rabbit_config)
    
