import pytesseract
import re
import json
import os
import sys
import subprocess

import textStuff as tf

from PIL import Image


class Tesseracter(object):

    def __init__(self):
        self.img = None
        self.standards_json = None
        self.standards_re = []

    def setImg(self, img):
        self.img = img

    def config(self, path):
        config_file = open(path, 'r')
        config_string = config_file.read()
        config_file.close()
        config_json = json.loads(config_string)

        self.standards_json = config_json['tesseracter']['standards']
        for key in self.standards_json:
            if self.standards_json[key] is not False:
                for reg in self.standards_json[key]:
                    self.standards_re.append(reg)

        return config_json

    def getText(self):
        rawText = pytesseract.image_to_string(self.img)
        switchedText = tf.textReplacer(rawText, self.standards_re)
        plates = {"good": [], "bad": []}

        for number in switchedText:
            for r in self.standards_re:
                reg = tf.regGenerator(r)
                regTmp = re.compile(reg, re.IGNORECASE)
                res = regTmp.match(number)
                if res is not None:
                    if number not in plates['good']:
                        plates['good'].append(number)
                else:
                    if number not in plates['bad']:
                        plates['bad'].append(number)

        return plates


if __name__ == '__main__':

    t = Tesseracter()

    t.config('config.json')

    im = Image.open('justNumber1.png')
    im = im.convert("P")
    t.setImg(im)
    res = t.getText()
    print(res)
else:
    pass
    """
    path = sys.argv[1]
    cmd = sys.argv[2]

    t = Tesseracter()

    t.config('config.json')

    if path:
        im = Image.open(path)
        im = im.convert("P")
        t.setImg(im)
        res = t.getText()

        if cmd:
            subprocess.call(['python', cmd, str(res)], shell=True)
    """
