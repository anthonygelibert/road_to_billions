#!/usr/bin/env python3.12

"""Wayne script."""

import logging
import sys

import click

from utils.log import setup_logging
from utils.retval import EX_OK, EX_SOFTWARE
from utils.version import get_version


@click.group(no_args_is_help=True, context_settings=dict(help_option_names=['-h', '--help']))
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose mode")
@click.version_option(get_version())
def cli(verbose: bool) -> None:
    """Tools for datasets."""
    setup_logging(verbose=verbose)


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        logging.info("[bold]Stopped by user.")
        sys.exit(EX_OK)
    except Exception as e:
        logging.critical(f"[bold red]:x:  Unexpected error: {type(e).__name__}: {e}", exc_info=True)
        sys.exit(EX_SOFTWARE)
