# dsmr-reader-docker

A docker-compose file in order to start the following application in Docker:  
dsmr-reader (https://github.com/dennissiemensma/dsmr-reader)

The Docker image can be found in the following link:
https://hub.docker.com/r/ualex73/dsmr-reader-docker/

Also it starts a PostgreSQL container for the application to store it's data.

You should first add the user you run Docker with on your host file system to the dialout group:
sudo usermod -aG dialout $(whoami)

After starting the containers with docker-compose, the dashboard is reachable at:  
http://\<hostname>:8888  

After starting the containers, don't forget to modify the default DSMR version (default is DSMR v4):  
http://\<hostname>:8888/admin/dsmr_datalogger/dataloggersettings/

---

dsmrdb in docker-compose is configured to use a docker volume. So when the application and docker containter have been removed, the postgres data still persists.

Also you could easily create a backup:  
- docker-compose stop dsmr
- docker exec -t dsmrdb pg_dumpall -c -U dsmrreader > /tmp/dump_`date +%d-%m-%Y""%H%M%S`.sql
- docker-compose start dsmr


Or drop the database and restore a backup:
- docker-compose stop dsmr
- docker exec -t dsmrdb dropdb dsmrreader -U postgres
- docker exec -t dsmrdb createdb -O dsmrreader dsmrreader -U dsmrreader
- cat /tmp/<your_dump>.sql | docker exec -i dsmrdb psql -U dsmrreader
- docker-compose start dsmr

---
The current configuration has been tested on Ubuntu 16.04 and 18.04

For Synology users:
- Drivers are necessary: http://jadahl.dscloud.me/drivers.html
- The docker-compose file must be set to version 2 instead of 3.
