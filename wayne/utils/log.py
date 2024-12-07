""" Log-related tools. """

import logging

import click
import rich.logging
from rich.console import Console


def setup_logging(verbose: bool = False):
    """ Setup console logging (DEBUG or INFO depending on verbose parameter). """
    log_level = logging.DEBUG if verbose else logging.INFO
    root_logger = logging.getLogger()

    # Set the log level
    root_logger.setLevel(log_level)

    # Purge old handler
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)

    # Add the rich handler
    rich_handler = rich.logging.RichHandler(level=log_level, rich_tracebacks=True, markup=True,
                                            tracebacks_suppress=[click.core],
                                            tracebacks_show_locals=log_level == logging.DEBUG, show_time=False,
                                            show_level=False, show_path=False, console=Console(width=120, tab_size=2))
    root_logger.addHandler(rich_handler)
