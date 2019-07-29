FROM ubuntu:18.04

MAINTAINER JasonX <jason@jasoncross.com>

RUN apt-get update && apt-get install -y sudo && rm -rf /var/lib/apt/lists/*

ENV DUET_HOSTNAME            duet.local
ENV DUET_PASSWORD            reprap
ENV SEND_IMAGE          false
ENV USE_ENERGY_MONITOR  false
ENV USE_IMAGE_LIGHT     false
ENV WRITE_STATISTIC     true
ENV PUSHOVER_APP_TOKEN  YOUR_APP_TOKEN
ENV PUSHOVER_USER       YOUR_PUSHOVER_USER
ENV SNAPSHOT_URL        http://hevocam/picture/1/current/
ENV ENERGY_URL          http://openhabianpi:8080/rest/items/Power_1_Counter/state
ENV STAT_FILE           /home/pi/bin/statistic.csv

COPY duetmonitor.py ~/bin/
COPY duetmonitor.cfg ~/.duetmonitor.cfg
COPY duetmonitor.service /lib/systemd/system/

CMD chmod u+x ~/bin/duetmonitor.py
CMD sudo chmod 644 /lib/systemd/system/duetmonitor.service
CMD python3 ~/bin/duetmonitor.py
