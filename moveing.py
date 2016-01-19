import cv2 as cv
import json

from multiprocessing import Pool


def detect(images, savePrv=False, num=0):

    gray = cv.cvtColor(images[0][num], cv.COLOR_BGR2GRAY)
    gray = cv.GaussianBlur(gray, (21, 21), 0)

    if savePrv:
        if images[1][num] is None:
            grayPrv = gray
        else:
            grayPrv = images[1][num]
    else:
        if images[1][num] is None:
            return None
        grayPrv = cv.cvtColor(images[1][num], cv.COLOR_BGR2GRAY)
        grayPrv = cv.GaussianBlur(grayPrv, (21, 21), 0)

    if savePrv:
        images[1][num] = gray

    try:
        frameDelta = cv.absdiff(grayPrv, gray)
    except:
        return False

    thresh = cv.threshold(frameDelta, 25, 255, cv.THRESH_BINARY)[1]
    thresh = cv.erode(thresh, None, iterations=2)

    (img, cnts, _) = cv.findContours(thresh.copy(),
                                     cv.RETR_EXTERNAL,
                                     cv.CHAIN_APPROX_SIMPLE)

    for c in cnts:
        if cv.contourArea(c) < 350:
            continue
        return True
    return False


class MovingDetector(object):

    def __init__(self):
        self.littleImgs = [None for i in range(0, 16)]
        self.littleImgsPrv = [None for i in range(0, 16)]
        self.roiForDrive = [0 for i in range(0, 16)]
        self.roiForLeave = [0 for i in range(0, 16)]

        self.lastChangeTime = 0
        self.movFlag = False

        self.configCount = 0
        self.activeRoi = []
        self.firstROI = 0
        self.roiCount = [0 for i in range(0, 16)]
        self.on = True
        self.config = None

    def doConfig(self, path):
        config_file = open(path, 'r')
        config_string = config_file.read()
        config_file.close()
        config_json = json.loads(config_string)
        self.config = config_json['moving']

        self.setActiveROI(self.config['roiForDrive'],
                          self.config['roiForLeave'])

        return self.config

    def setActiveROI(self, drive, leave):
        self.activeRoi = drive + leave
        self.activeRoi.sort()

    def processing(self, image):
        """ Do not use this version """

        roiCount = 0
        direction = 'none'
        images = []

        g = self.gDivadeImg(image.copy(), self.activeRoi)

        if self.on:
            if self.activeRoi:
                for roi in self.activeRoi:
                    self.littleImgs[roi] = next(g)
                    images.append([self.littleImgs,
                                   self.littleImgsPrv])
                    self.littleImgsPrv[roi] = self.littleImgs[roi]
                    roiCount += 1
                p = Pool(roiCount)
                results = p.map(detect, images)
                p.close()
            if True in results:
                return [True, direction]
            else:
                return [False, direction]
        else:
            return [False, 'none']

    def processing_v2(self, image):
        """ Better use this version """

        directionDetectionFlag = 1
        direction = 'none'
        results = []

        try:
            g = self.gDivadeImg(image.copy(), self.activeRoi)

            if self.on:
                if self.activeRoi:
                    for roi in self.activeRoi:
                        self.littleImgs[roi] = next(g)
                        res = detect([self.littleImgs,
                                      self.littleImgsPrv],
                                      True, roi)
                        results.append(res)
                        if directionDetectionFlag:
                            if res:
                                directionDetectionFlag = 0
                                try:
                                    self.roiForDrive.index(roi)
                                    direction = 1
                                except ValueError:
                                    direction = 2

                if True in results:
                    return [True, direction]
                else:
                    return [False, direction]
            else:
                return [False, 'none']
        except AttributeError:
            print('Image type ERROR')
            return [False, 'none']

    def gDivadeImg(self, img, number):
        row, cols, depth = img.shape
        width = cols / 5
        high = row / 5
        count = 0

        for i in range(0, 5):
            if number[count] < 5:
                yield (img[(0):
                           (high),
                           (number[count] * width):
                           (width * (number[count] + 1))])
                count += 1
        for i in range(0, 3):
            if number[count] < 8:
                yield (img[(high * (number[count] - 5 + 1)):
                           (high * (number[count] - 5 + 1) + high),
                           (cols - width):
                           (cols)])
                count += 1
        for i in range(0, 5):
            if number[count] < 13:
                yield (img[(row - high):
                           (row),
                           ((4 - number[count] + 8) * width):
                           (width * ((4 - number[count] + 8) + 1))])
                count += 1
        for i in range(0, 3):
            if number[count] < 16:
                yield (img[(high * (-number[count] + 15)):
                           ((high * (-number[count] + 15)) + high),
                           (0):
                           (width)])
                count += 1