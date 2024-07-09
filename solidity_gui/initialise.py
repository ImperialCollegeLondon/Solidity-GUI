"""Routines for global application setup."""

import logging
from multiprocessing import cpu_count

from . import config
from .logger import initialise_logging


def initialise_app(process_name: str | None = None) -> None:
    """Perform global setup for application."""
    # Configure program log
    initialise_logging(process_name)

    from . import plugins  # noqa: F401

    # Set number of CPUs to run Solidity on to the number of CPUs available
    config.NUM_CPUS = cpu_count()
    logging.info(f"Using {config.NUM_CPUS} CPUs for Solidity")
