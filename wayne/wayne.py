#!/usr/bin/env python3.12

"""Wayne script."""

import os
import sys

import click
import pandas as pd
import plotly.graph_objects as go
# noinspection PyPackageRequirements
from binance.spot import Spot as Client
from rich import print, traceback  # noqa:A004

assert "API_KEY" in os.environ, "Please add API_KEY environment variable"
assert "API_SECRET" in os.environ, "Please add API_SECRET environment variable"


@click.group(no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose mode")
def cli(*, verbose: bool) -> None:
    """Tools for datasets."""
    traceback.install(width=200, show_locals=verbose)


@cli.command()
def btcusdt() -> None:
    """Display BTC2USD curve."""
    client = Client(os.environ["API_KEY"], os.environ["API_SECRET"])
    column_names = ["Open time", "Open price", "High price", "Low price", "Close price", "Volume", "Kline close time",
                    "Quote asset volume", "Number of trades", "Taker buy base asset volume",
                    "Taker buy quote asset volume", "Ignore"]
    # noinspection PyArgumentList,PyUnresolvedReferences
    kls = pd.DataFrame(client.ui_klines(symbol="BTCUSDT", interval="1d", limit=1000), columns=column_names)
    kls["Open time"] = pd.to_datetime(kls["Open time"], unit="ms")
    candlestick = go.Candlestick(x=kls["Open time"], open=kls["Open price"], high=kls["High price"],
                                 low=kls["Low price"], close=kls["Close price"])
    fig = go.Figure(data=[candlestick])
    fig.update_layout(width=800, height=600, title="BTCUSDT", yaxis_title="Price")
    fig.show()


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        print("[bold]Stopped by user.")
        sys.exit(0)
