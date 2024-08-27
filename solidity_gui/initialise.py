"""Routines for global application setup."""

from .logger import initialise_logging


def initialise_app(process_name: str | None = None) -> None:
    """Perform global setup for application."""
    # Configure program log
    initialise_logging(process_name)

    from . import plugins  # noqa: F401
