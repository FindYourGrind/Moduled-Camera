import cv2 as cv
from PIL import Image
import numpy as np
import copy
import json
import plateToText


class PlaitNumberFinder(object):
    """Estimator of string of plait number. OpenCV 3.0.0"""

    def __init__(self):
        self.treshImg = 0
        self.plaitNumberImage = 0
        self.plaitNumberHigh = 1
        self.plaitNumberWidth = 1
        self.config = {}

    def doConfig(self, path):
        config_file = open(path, 'r')
        config_string = config_file.read()
        config_file.close()
        config_json = json.loads(config_string)
        self.config = config_json['plater']
        return self.config

    def setHaarCascade(self, cascadeHaar):
        self.number_cascade = cv.CascadeClassifier(cascadeHaar)

    def detectPlaitNumber(self, img):
        plaitNumber = self.number_cascade.detectMultiScale(img, 1.3, 5)
        print(plaitNumber)
        for (x, y, w, h) in plaitNumber:
            self.plaitNumberImage = img[y:y + h, x:x + w]
            height, width = self.plaitNumberImage.shape[:2]
            self.plaitNumberImage = cv.resize(self.plaitNumberImage, (width * 100 / height, 100),
                                              interpolation=cv.INTER_CUBIC)
            self.saveImgInJPG("plate.jpg", self.plaitNumberImage)
            return self.plaitNumberImage
        else:
            print("Plate Number Not Finded")
            return None

    def doGrayImg(self, img):
        return cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    def findEdges(self, grayImg, k1, k2):
        return cv.Canny(grayImg, k1, k2)

    def doThreshold(self, grayImg, k1, k2):
        return cv.threshold(grayImg, k1, k2, cv.THRESH_BINARY)[1]

    def findContours(self, treshImage):
        rows, cols = treshImage.shape[:2]
        if rows > 0 and cols > 0:
            image, contours, hierarchy = cv.findContours(treshImage, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
            if isinstance(contours, type(None)):
                print("contours not found")
                return None
            print("Finded contours")
            return contours
        return None

    def findPoligons(self, contours, grayImg):
        if not isinstance(contours, type(None)):
            for cnt in contours:
                rect = cv.minAreaRect(cnt)
                k = rect[1]
                print(k)
                if 2.8 < float(max(k) / (min(k) + 0.0000001)) < 8.0 and min(k) > 43:
                    h = min(k)
                    w = max(k)
                    x = rect[0][0] - w / 2
                    y = rect[0][1] - h / 2
                    self.plaitNumberHigh = h
                    self.plaitNumberWidth = w
                    print("Finded poligon")
                    return(grayImg[y:y + h, x:x + w])
        print("Poligon not finded")
        return 0

    def findLinesHough(self, edgesImg):
        lines = cv.HoughLines(edgesImg, 1, np.pi / 180, 200)
        if isinstance(lines, type(None)):
            print("lines no found")
            return 0

    def estLine(lines):
        t = []
        l = []
        for line in lines:
            for rho, theta in line:
                l.append(rho)
                t.append(theta)
        return t, l

    def findLines(self, lines, img, edges):
        t, l = self.estLine(lines)
        rows, cols, depth = img.shape
        M = cv.getRotationMatrix2D((cols / 2, rows / 2), (t[0] - 1.57079637) * 180 / np.pi, 1)
        res = cv.warpAffine(img, M, (cols, rows))
        lines = cv.HoughLines(res, 1, np.pi / 180, 200)
        t, l = self.estLine(lines)
        return img[min(l):max(l), ]

    def getPlaitNumberByLiterals(self, contours, img, k1):

        count = 0
        x_mass = []
        x_massSorted = []
        literals_mass = []

        if self.plaitNumberHigh is 1 or self.plaitNumberWidth is 1:
            self.plaitNumberHigh = 50
            self.plaitNumberWidth = 300

        if not isinstance(contours, type(None)):

            minH = int(self.plaitNumberHigh * 0.5)
            maxH = int(self.plaitNumberHigh * 0.9)

            minW = int(self.plaitNumberWidth * 0.05)
            maxW = int(self.plaitNumberWidth * 0.5)

            for cnt in contours:
                x, y, w, h = cv.boundingRect(cnt)

                if h in range(minH, maxH) and w in range(minW, maxW):
                    x_mass.append(x)
                    count += 1
                    literal = img[y:y + h, x:x + w]
                    literal = cv.resize(literal, (30, 45))
                    literals_mass.append(literal)

        tmp = x_mass[:]
        tmp.sort()

        for i in range(0, tmp.__len__()):
            if i < (tmp.__len__() - 1):
                d = tmp[i + 1] - tmp[i]
                if d < 10:
                    x_mass.remove(tmp[i + 1])

        if 8 < x_mass.__len__() < 7:
            return "None"
        numberForParsing = np.zeros((55, (40 * x_mass.__len__() + 5)), np.uint8)
        rows, cols = numberForParsing.shape
        numberForParsing[0:0 + rows, 0:0 + cols] = 255

        for i in range(0, x_mass.__len__()):
            x_massSorted.append(x_mass.index(min(x_mass)) + 1)
            x_mass[x_mass.index(min(x_mass))] = 1000000
            tmp = literals_mass[x_massSorted[i] - 1]
            x = 40 * i + 3
            numberForParsing[5:50, x:x + 30] = tmp

        self.saveImgInJPG('justNumber.jpg', numberForParsing)
        self.openJPGsavePNG('justNumber.jpg', 'justNumber.png')
        numberForParsing = cv.imread('justNumber.jpg')
        return numberForParsing

    def saveImgInJPG(self, name, img):
        cv.imwrite(name, img)

    def openJPGsavePNG(self, nameJPG, namePNG):
        im = Image.open(nameJPG)
        im.save(namePNG)

    def openImgInPNG(self, name):
        im = Image.open(name)
        return im.convert("P")

    def resizeImg(self, img, w, h):
        return cv.resize(img, (w, h), interpolation=cv.INTER_CUBIC)


def plateFinder(finder, image):

    cutNumberImg = finder.detectPlaitNumber(image)

    if not isinstance(cutNumberImg, type(None)):

        rows, cols = cutNumberImg.shape[:2]
        angle = float(finder.config['angle'])

        matrix = cv.getRotationMatrix2D((cols / 2, rows / 2), angle, 1)
        cutNumberImg = cv.warpAffine(cutNumberImg, matrix, (cols, rows))

        cutNumberImgGrey = finder.doGrayImg(cutNumberImg)
        cutNumberImgTresh = finder.doThreshold(cutNumberImgGrey, 120, 255)
        finder.treshImg = copy.copy(cutNumberImgTresh)
        contours = finder.findContours(cutNumberImgTresh)
        justNumber = finder.findPoligons(contours, finder.treshImg)

        cv.imwrite('test1.jpg', justNumber)

        if not isinstance(justNumber, type(0)):
            row, cols = justNumber.shape
            if row > 0 and cols > 0:

                cutNumberImgTresh = copy.copy(justNumber)
                contours = finder.findContours(cutNumberImgTresh)
                justNumber = finder.getPlaitNumberByLiterals(contours, justNumber, 140)

                if justNumber is not "None":

                    finder.saveImgInJPG('justNumber.jpg', justNumber)
                    finder.openJPGsavePNG('justNumber.jpg', 'justNumber.png')
                    numberForParsing = finder.openImgInPNG('justNumber.png')

                    return numberForParsing


def plate(data):

    finder = PlaitNumberFinder()
    finder.doConfig('config.json')
    finder.setHaarCascade(finder.config['haarPath'])

    dataForTess = plateFinder(finder, data)

    t = plateToText.Tesseracter()

    t.config('config.json')

    im = Image.open('justNumber.png')
    im = im.convert("P")
    t.setImg(im)
    res = t.getText()
    print(res)


if __name__ == '__main__':
    image = cv.imread('plateTest.jpg')
    plate(image)
else:
    pass