import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--remake-config-file", action="store_true")
parser.add_argument("--reload-textures", action="store_true")
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument("-v", "--verbose", action="count", default=0)

parser.add_argument("--replay", default=None)


def parse():
    global args
    args = parser.parse_args()
