"""Example code which just runs Solidity with the specified arguments."""
import sys

from . import run

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
