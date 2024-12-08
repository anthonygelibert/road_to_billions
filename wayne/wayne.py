#!/usr/bin/env python3.12

"""Wayne script."""

import sys

import click
from rich import print, traceback  # noqa:A004

from utils.retval import EX_OK
from utils.version import get_version


@click.group(no_args_is_help=True, context_settings=dict(help_option_names=['-h', '--help']))
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose mode")
@click.version_option(get_version())
def cli(verbose: bool) -> None:
    """Tools for datasets."""
    traceback.install(width=200, show_locals=verbose)


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        print("[bold]Stopped by user.")
        sys.exit(EX_OK)
