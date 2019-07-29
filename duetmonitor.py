#!/usr/bin/env python3

import os
import sys
import time
import configparser
import datetime
import json
import requests
import http.client
import urllib
import csv

printimage = '/tmp/printimage.jpg'

def main(argv):
    print('DuetMonitor started.')

    # check and initially load config
    global config
    readCheckConfig()

    printing = False
    filename = None
    energy_monitor_start = 0.0
    printDuration = 0

    global hostname
    global reprap_pass

    # main loop
    while True:
        try:
            reloadConfig()

            hostname = os.environ['DUET_HOSTNAME']
            reprap_pass = os.environ['DUET_PASSWORD']

            requests.get('http://' + hostname + '/rr_connect?password=' + reprap_pass + '&time=' + datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'))
            status = json.loads(requests.get('http://' + hostname + '/rr_status?type=1').text)['status']
            if status == 'P' and not printing:
                printing = True
                startTime = datetime.datetime.now()
                filename = os.path.basename(json.loads(requests.get('http://' + hostname + '/rr_fileinfo').text)['fileName'])
                printDuration = 0
                if (useEnergyMonitor()):
                    energy_monitor_start = getCurrentEnergy()
                print('Print started:', filename)
            if status == 'I' and printing:
                print('Print finished:', filename)

                if useImage():
                    if useLightForImage():
                        # turn light on
                        switchLight(255)
                        # make sure it's on => wait 5sec
                        time.sleep(15)
                    # take a photo
                    files = getImage()

                    if useLightForImage():
                        # turn light off
                        switchLight(0)
                else:
                    files = None

                message = 'Print of {} finished!\nDuration: {}'.format(filename, datetime.timedelta(seconds=printDuration))
                energy_use = 0.0
                if (useEnergyMonitor()):
                    energy_use = float(getCurrentEnergy()-energy_monitor_start)
                    message += '\nEnergy used: {:.2f}Wh'.format(energy_use)

                r = requests.post("https://api.pushover.net/1/messages.json", data = {
                    "token": os.environ['PUSHOVER_APP_TOKEN'],
                    "user": os.environ['PUSHOVER_USER'],
                    "message": message
                },
                files = files)
                print(r.text)

                if os.path.isfile(printimage):
                    os.remove(printimage)

                if (writeStatistic()):
                    #(filename, start, end, duration, energy)
                    writeStatisticToFile(filename, startTime, datetime.datetime.now(), printDuration, energy_use)

                printing = False
                filename = None
            if status == 'P' and printing:
                # get printDuration of current file directly from printer
                printDuration = json.loads(requests.get('http://' + hostname + '/rr_fileinfo').text)['printDuration']
            requests.get('http://' + hostname + '/rr_disconnect')
        except Exception as e:
            print('ERROR', e)
            pass
        time.sleep(60)
        print('...')

def getImage():
    files = None
    try:
        img_data = requests.get(os.environ['SNAPSHOT_URL']).content
        with open(printimage, 'wb') as handler:
            handler.write(img_data)
        files = {
            "attachment": ("printimage.jpg", open(printimage, "rb"), "image/jpeg")
        }
    except Exception as ei:
        print('Could not get image', ei)
        files = None

    return files


def readCheckConfig():
    reloadConfig()

    if not checkConfig():
        return False

    print("Configuration read sucessfull")

def checkConfig():
    valid = True
    # hostname must be set
    if (os.environ['DUET_HOSTNAME'] is ''):
        print ("Duet hostname is not set")
        valid = False

    # password must be set
    if (os.environ['DUET_PASSWORD'] is ''):
        print ("Duet password is not set")
        valid = False

    # pushover app_token must be set
    if (os.environ['PUSHOVER_APP_TOKEN'] is ''):
        print ("Pushover app_token is not set")
        valid = False

    # pushover user must be set
    if (os.environ['PUSHOVER_USER'] is ''):
        print ("Pushover user is not set")
        valid = False

    # check image settings
    if (useImage()):
        if (os.environ['SNAPSHOT_URL'] is ''):
            print ("Images should be used but snapshot_url is not set")
            valid = False

    # check energy monitor settings
    if (useEnergyMonitor()):
        if (os.environ['ENERGY_URL'] is ''):
            print ("Energy monitor should be used but energy_url is not set")
            valid = False

    # check statistic settings
    if (writeStatistic()):
        if (os.environ['WRITE_STATISTIC'] is ''):
            print ("Statistics should be written but file is not set")
            valid = False

    if (not valid):
        raise Exception('Configuration Error')

def switchLight(value):
    requests.get('http://' + hostname + '/rr_gcode?gcode=M106 P2 S' + str(value))

def reloadConfig():
    global config
    config = configparser.ConfigParser()
    config.read(['duetmonitor.cfg', os.path.expanduser('~/.duetmonitor.cfg')])

def useLightForImage():
    return os.environ['USE_IMAGE_LIGHT']

def useImage():
    return os.environ['SEND_IMAGE']

def useEnergyMonitor():
    return os.environ['USE_ENERGY_MONITOR']

def writeStatistic():
    return os.environ['WRITE_STATISTIC']

def writeStatisticToFile(filename, start, end, duration, energy):
    print ("Write statistic to file called")
    csv_file = os.environ['STAT_FILE']
    write_header = False

    if not os.path.isfile(csv_file):
        write_header = True


    #datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

    with open(csv_file, 'a') as csvHandler:
        newFileWriter = csv.writer(csvHandler, delimiter=';')
        if write_header:
            newFileWriter.writerow(['filename', 'start', 'end', 'duration', 'energy'])

        newFileWriter.writerow([filename, start.strftime('%Y-%m-%d %H:%M:%S'), end.strftime('%Y-%m-%d %H:%M:%S'), duration, '{:.2f}'.format(energy)])

    print ("Write statistic to file finished")


def getCurrentEnergy():
    try:
        return float(requests.get(os.environ['ENERGY_URL']).text)
    except Exception as ei:
        print ('Could not get current energy')

    return 0.0

if __name__ == "__main__":
    main(sys.argv)
