"""Example code which just runs Solidity with the specified arguments."""
from pathlib import Path
from sys import argv

from ..logger import initialise_logging
from . import run_solidity

if __name__ == "__main__":
    initialise_logging()

    container = run_solidity(Path(argv[1]), Path(argv[2]), Path(argv[3]), Path(argv[4]))

    # Print stdout and stderr and wait for execution to finish
    container.attach()
