# -*- coding: utf-8 -*-
import requests
import json

gConfigPath = '/home/pi/Dev/Moduled-Camera/config.json'


def doConfig(path, typeOfConfig):
    config_file = open(path, 'r')
    config_string = config_file.read()
    config_file.close()
    config_json = json.loads(config_string)
    config = config_json[typeOfConfig]
    return config


def doRequest(data):
    configRequester = doConfig(gConfigPath, 'requester')
    configGeneral = doConfig(gConfigPath, 'general')

    r = requests.post(configRequester['url'].strip(),
                     json={
                        "dev_id": configGeneral['cameraID'],
                        "place": data['place'],
                        "car_plate": data['goodPlates'],
                        "car_plate_raw": data['badPlates'],
                        "direction": data['direction'],
                        "img": data['image']
                     })

    if r == 200:
        return True
    else:
        return False


if __name__ == "__main__":
    pass
else:
    pass