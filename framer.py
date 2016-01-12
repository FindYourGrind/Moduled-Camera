import time
import io
import picamera
import picamera.array
import os
import moveing
import cv2 as cv
import numpy as np

from multiprocessing import Process
from PIL import Image

def init_camera(camera):
    ret = {}
    ret['resolution'] = camera.resolution = (2592, 1944)
    ret['framerate'] = camera.framerate = 15
    ret['raw'] = io.BytesIO()
    ret['format'] = 'jpeg'
    ret['port'] = False
    time.sleep(0.1)
    return ret


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


def fun(path):
    img = cv.imread('/mnt/ramdisk/pic.jpg', )
    time.sleep(1)
    print(path)


if __name__ == '__main__':

    f = open('/mnt/ramdisk/pic.jpeg', 'w+')
    f.close()

    fps = calcFPS()
    detector = moveing.MovingDetector()

    with picamera.PiCamera() as camera:

        camera.resolution = (1280, 760)
        camera.framerate = 30
        camera.quality = 100
        raw = open('/mnt/ramdisk/pic.jpg', 'w')
        #raw = picamera.array.PiRGBArray(camera)
        #raw = io.BytesIO()

        for fil in camera.capture_continuous(raw,
                                             format="jpeg",
                                             use_video_port=True):

            #f = open('/mnt/ramdisk/pic.jpg', 'r')
            #img = f.read()
            #f.close()

            #img = Image.open('/mnt/ramdisk/pic.jpg').convert('RGB')
            #img = np.array(img)

            t = time.time()
            img = cv.imread('/mnt/ramdisk/pic.jpg')
            print(('ImRead:' + str(time.time() - t)))
            #print(time.time())

            #t = time.time()
            #detector.processing(img)
            #print(('v1 time:' + str(time.time() - t)))

            t = time.time()
            print(detector.processing_v2(img))
            print(('v2 time:' + str(time.time() - t)))

            #p = Process(target=fun, args=('/img',))
            #p.start()

            raw.seek(0)

            #print((fps.next()))

        raw.close()


