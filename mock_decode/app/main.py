import sys
import os


if __name__ == "__main__":
    print(sys.argv)
    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))
