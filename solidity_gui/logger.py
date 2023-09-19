"""Set up the program's logger."""
import logging
from datetime import datetime

from platformdirs import user_log_path

from . import config


def initialise_logging(process_name: str | None) -> None:
    """Configure the program's logger.

    Args:
      process_name: applied as a suffix to the logging filename if provided
    """
    log_path = user_log_path(config.APP_NAME.replace(" ", "-"), config.APP_AUTHOR)
    log_path.mkdir(parents=True, exist_ok=True)
    suffix = f"-process-{process_name}" if process_name else ""
    filename = log_path / (
        f"{datetime.now().strftime('%Y%m%d_%H-%M-%S')}" + suffix + ".log"
    )

    # Log to console and file
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(filename), logging.StreamHandler()],
        force=True,  # make sure config is applied in background processes
    )

    logging.info(f"Saving log to {filename}")
