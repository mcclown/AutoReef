#! /bin/bash

sudo nameko run --config ./config/tempProbe1.yaml Services.Integrations.TempSensor:DS18B20
