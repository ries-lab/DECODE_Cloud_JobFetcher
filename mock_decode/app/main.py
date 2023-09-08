import sys
import os
from pathlib import Path


if __name__ == "__main__":
    print(sys.argv)
    print(os.getcwd())
    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))

    p_in = Path("/data/decode.txt")
    p_out = Path("/output/decode.txt")

    with p_out.open("w") as f:
        with p_in.open("r") as f_in:
            f.write(f_in.read())
        f.write("\n".join(sys.argv))
        f.write(os.getcwd())
        for name, value in os.environ.items():
            f.write("{0}: {1}".format(name, value))

    print("Done")
