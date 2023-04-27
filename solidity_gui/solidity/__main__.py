"""Example code which just runs Solidity with the specified arguments."""
from pathlib import Path
from sys import argv

from . import run_solidity

if __name__ == "__main__":
    run_solidity(Path(argv[1]), Path(argv[2]), Path(argv[3]), Path(argv[4]))
