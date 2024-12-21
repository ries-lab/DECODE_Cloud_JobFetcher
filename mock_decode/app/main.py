import os
import sys
from pathlib import Path

if __name__ == "__main__":
    print(sys.argv)
    print(os.getcwd())
    for name, value in os.environ.items():
        print("{0}: {1}".format(name, value))

    # fake some output
    print("Faking some output")
    paths_out = [Path(p) for p in ["/data/output", "/data/log", "/data/artifact"]]
    for p in paths_out:
        p_rand = p / "random.txt"
        p_rand.write_text("Random text.")

    # print filesystem
    print("Files in /data")
    paths = sorted(Path("/data").rglob("*"))
    [print(p) for p in paths]

    print("Done")
