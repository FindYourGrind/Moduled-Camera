import time
import io
import picamera
import picamera.array
import os
import moveing
import cv2 as cv
import plater
import shutil

from multiprocessing import Process, Pool


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


def action(paths):

    p = Pool(5)
    #p.map(plater.plate, ['/mnt/ramdisk/pic1.jpg',
    #                     '/mnt/ramdisk/pic2.jpg',
    #                     '/mnt/ramdisk/pic3.jpg',
    #                     '/mnt/ramdisk/pic4.jpg',
    #                     '/mnt/ramdisk/pic5.jpg'])
    results = p.map(plater.plate, ['/home/pi/Dev/Moduled-Camera/plateTest.jpg',
                         '/mnt/ramdisk/pic2.jpg',
                         '/mnt/ramdisk/pic3.jpg',
                         '/mnt/ramdisk/pic4.jpg',
                         '/mnt/ramdisk/pic5.jpg'])
    p.close()

    print(results)


if __name__ == '__main__':

    #f = open('/mnt/ramdisk/pic.jpeg', 'w+')
    #f.close()

    fps = calcFPS()
    detector = moveing.MovingDetector()

    with picamera.PiCamera() as camera:

        recordFlag = False
        snapsCount = 0
        snapsArr = []
        movData = []

        camera.resolution = (800, 600)
        camera.framerate = 20
        camera.quality = 100
        raw = open('/mnt/ramdisk/pic.jpg', 'r+')

        for fil in camera.capture_continuous(raw,
                                             format="jpeg",
                                             use_video_port=True):

            if not recordFlag:
                #t = time.time()
                img = cv.imread('/mnt/ramdisk/pic.jpg')
                #print(('ImRead:' + str(time.time() - t)))

                #t = time.time()
                movData = detector.processing_v2(img)
                #print(('v2 time:' + str(time.time() - t)))

                if True in movData:
                    snapsArr = []
                    snapsCount = 5
                    recordFlag = True

            if recordFlag:
                if snapsCount:
                    shutil.copyfile('/mnt/ramdisk/pic.jpg',
                                    '/mnt/ramdisk/pic' +
                                    str(snapsCount) + 'jpg')
                    snapsCount -= 1
                else:
                    recordFlag = False
                    p = Process(target=action, args=('hi',))
                    p.start()

            raw.seek(0)
            #print((next(fps)))

        raw.close()


