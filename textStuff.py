import re

def textReplacer(string, standards):
    res = []
    #delete= ['\n', '\r', '`', '\'', '*', '^', '$', '&', '%', '#', '@', ]
    #replace = []

    s = string.strip()
    s = s.replace('\n', '')
    s = s.replace('?', '7')
    s = s.replace('^\[a-z]', '')
    res.append(s)
    return res


def regGenerator(standard):
    tmp = standard.replace("L", "[a-z]")
    tmp = tmp.replace("D", "\d")
    return tmp


if __name__ == "__main__":
    pass
else:
    pass