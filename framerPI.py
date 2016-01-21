import time
import picamera
import picamera.array
import os
import moveing
import cv2 as cv
import plater
import shutil
import json
import requester
import errno
import base64

from multiprocessing import Process, Pool
from multiprocessing.managers import BaseManager

from socketIO_client import SocketIO, LoggingNamespace

gConfigPath = '/home/pi/Dev/Moduled-Camera/config.json'


class Sensor(object):

    def __init__(self):
        self.sensorEvent = False

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Sensor, cls).__new__(cls)
        return cls.instance

    def getEvent(self):
        return self.sensorEvent

    def setEvent(self):
        self.sensorEvent = True

    def resetEvent(self):
        self.sensorEvent = False


class Config(object):

    def __init__(self):
        self.configEvent = False

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Config, cls).__new__(cls)
        return cls.instance

    def getEvent(self):
        return self.configEvent

    def setEvent(self):
        self.configEvent = True

    def resetEvent(self):
        self.configEvent = False


class MyManager(BaseManager):
    pass


def Manager():
    m = MyManager()
    m.start()
    return m


MyManager.register('Sensor', Sensor)
MyManager.register('Config', Config)


def pSocketIO(sensorData, configData):

    def sensor():
        sensorData.setEvent()

    def setConfig(data):
        print(data)
        #writeConfigJSON(gConfigPath, data)
        #configData.setEvent()

    def getConfig():
        config = readConfigJSON(gConfigPath)
        socketIO.emit('config', config)

    socketIO = SocketIO('192.168.1.146', 8081, LoggingNamespace)
    socketIO.on('sensor', sensor)
    socketIO.on('set_config', setConfig)
    socketIO.on('get_config', getConfig)
    socketIO.wait()


def readConfigJSON(path):
    config_file = open(path, 'r')
    config_string = config_file.read()
    config_file.close()
    return config_string


def writeConfigJSON(path, data):
    config_file = open(path, 'w')
    config_file.write(data)
    config_file.close()


def doConfig(path, typeOfConfig):
    config_file = open(path, 'r')
    config_string = config_file.read()
    config_file.close()
    config_json = json.loads(config_string)
    config = config_json[typeOfConfig]
    return config


def calcFPS():
    timePrv = time.time()
    fps = 0
    fpsPrv = 0
    while True:
        timeAct = time.time()
        if (timeAct - timePrv) > 5:
            timePrv = timeAct
            yield ((fps / 5))
            fpsPrv = fps / 5
            fps = 0
        else:
            fps += 1
            yield fpsPrv


def getLastModifieTime(path):
    return os.path.getmtime(path)


def generateRequestData(results, direction, workers):

    folderWithGoodPictureFlag = True
    folderWithGoodPicture = None
    folderWithBadPicture = None

    count = 0

    data = {}

    data['place'] = 1

    data['goodPlates'] = []
    data['badPlates'] = []

    for chunk in results:
        if chunk:
            if chunk['good']:
                folderWithGoodPicture = workers - count
                folderWithGoodPictureFlag = False
                data['goodPlates'].append(chunk['good'])
            if chunk['bad']:
                if folderWithGoodPictureFlag:
                    folderWithBadPicture = workers - count
                data['badPlates'].append(chunk['bad'])
        count += 1

    data['direction'] = direction

    actualFolder = 0
    encodedImage = 'none'

    if folderWithGoodPicture:
        actualFolder = folderWithGoodPicture
    elif folderWithBadPicture:
        actualFolder = folderWithBadPicture

    with open('/mnt/ramdisk/' + str(actualFolder) + '/forServer.jpg', 'rb') as image:
        encodedImage = base64.b64encode(image.read())

    data['image'] = encodedImage

    return data


def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def action(paths, direction, workers, req):
    p = Pool(workers)
    results = p.map(plater.plate, paths)
    p.close()

    for result in results:
        if result is not False:
            data = generateRequestData(results, direction, workers)
            if req:
                requester.doRequest(data)
            break


if __name__ == '__main__':

    while True:
        config = doConfig(gConfigPath, 'general')

        dataManager = Manager()
        sensorData = dataManager.Sensor()
        configData = dataManager.Config()

        recordFlag = False
        snapsCount = 0
        snapsArr = []
        movData = []
        dataForPlater = []
        direction = 'none'

        workers = config['workers']

        pSocket = Process(target=pSocketIO, args=(sensorData, configData, ))
        pSocket.start()

        for i in range(1, 31):
            mkdir(config['imagesPath'] + str(i))

        fps = calcFPS()
        detector = moveing.MovingDetector()
        detector.doConfig(gConfigPath)

        with picamera.PiCamera() as camera:

            camera.resolution = (config['resolution']['width'],
                                 config['resolution']['height'])
            camera.framerate = config['framerate']
            camera.quality = config['quality']

            raw = open(config['imagesPath'] + 'pic.jpg', 'w')

            for fil in camera.capture_continuous(raw,
                                                 format="jpeg",
                                                 use_video_port=config['videoPort']):

                if not recordFlag:

                    img = cv.imread(config['imagesPath'] + 'pic.jpg')

                    if config['sensor']:
                        if sensorData.getEvent():
                            sensorData.resetEvent()
                            snapsArr = []
                            snapsCount = workers
                            recordFlag = True
                            time.sleep(config['delay'] / 1000)
                    else:
                        moving, direction = detector.processing_v2(img)

                        if moving:
                            snapsArr = []
                            snapsCount = workers
                            recordFlag = True

                if recordFlag:
                    if snapsCount:
                        name = config['imagesPath'] + str(snapsCount) + '/pic' + str(snapsCount) + 'jpg'
                        dataForPlater.append([name, snapsCount])
                        shutil.copyfile(config['imagesPath'] + 'pic.jpg', name)
                        snapsCount -= 1
                    else:
                        recordFlag = False
                        p = Process(target=action, args=(dataForPlater,
                                                         direction,
                                                         workers,
                                                         config['doRequest']))
                        p.start()
                        dataForPlater = []
                        time.sleep(1)

                if configData.getEvent():
                    print('reconfig')
                    break

                raw.seek(0)
                #print((next(fps)))

            raw.close()


