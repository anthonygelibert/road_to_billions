# coding=utf-8

""" Wayne script. """

import json
import logging
import sys
from pathlib import Path

import click
# noinspection PyPackageRequirements
from binance import Client

import utils


@click.group(no_args_is_help=True, context_settings=dict(help_option_names=['-h', '--help']))
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose mode")
@click.version_option(utils.get_version())
def cli(verbose: bool) -> int:
    """ Tools for datasets. """
    utils.setup_logging(verbose)
    return utils.EX_OK


@cli.group(context_settings=dict(help_option_names=['-h', '--help']))
def test() -> None:
    """ Group for the test commands. """
    pass


@test.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.argument("output_json", type=utils.OutputFile(suffix=".json", exist_ok=True))
def save_exchange_info(output_json: Path) -> int:
    """ Save the exchange information as JSON file. """
    config = utils.get_config()
    client = Client(api_key=config.api_key, api_secret=config.api_secret)

    output_json.write_text(json.dumps(client.get_exchange_info(), indent=2))

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
