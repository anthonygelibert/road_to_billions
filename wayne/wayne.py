# coding=utf-8

""" Wayne script. """

import logging
import sys

import click

import utils


@click.group(no_args_is_help=True, context_settings=dict(help_option_names=['-h', '--help']))
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose mode")
@click.version_option(utils.get_version())
def cli(verbose: bool) -> int:
    """ Tools for datasets. """
    return utils.EX_OK


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        logging.info("[bold]Stopped by user.")
        sys.exit(utils.EX_OK)
    except Exception as e:
        logging.exception(f"[bold red]:x:  Unexpected error: {type(e).__name__}: {e}")
        sys.exit(utils.EX_SOFTWARE)

if __name__ == '__main__':
    print(utils.get_config())
