#!/bin/bash

cd /home/pi/app/waApp_api
docker compose down
git pull origin main
docker compose up --build