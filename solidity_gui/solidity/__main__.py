"""Example code which just runs Solidity with the specified arguments."""

import atexit
from pathlib import Path
from sys import argv

from ..logger import initialise_logging
from . import remove_container_sync, run_solidity_no_stream

if __name__ == "__main__":
    initialise_logging(None)

    container = run_solidity_no_stream(
        Path(argv[1]), Path(argv[2]), Path(argv[3]), Path(argv[4]), int(argv[5])
    )

    # Remove container even if something goes wrong
    atexit.register(remove_container_sync)

    # Print stdout and stderr and wait for execution to finish
    container.attach()
