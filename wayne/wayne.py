#!/usr/bin/env python3.12

"""Wayne script."""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
# noinspection PyPackageRequirements
from binance.spot import Spot as Client
from rich import print, traceback  # noqa:A004

assert "API_KEY" in os.environ, "Please add API_KEY environment variable"
assert "API_SECRET" in os.environ, "Please add API_SECRET environment variable"


def print_curve() -> None:
    """Display BTC2USD curve."""
    client = Client(os.environ["API_KEY"], os.environ["API_SECRET"])
    column_names = ["Open time", "Open price", "High price", "Low price", "Close price", "Volume", "Kline close time",
                    "Quote asset volume", "Number of trades", "Taker buy base asset volume",
                    "Taker buy quote asset volume", "Ignore"]
    # noinspection PyArgumentList,PyUnresolvedReferences
    kls = pd.DataFrame(client.ui_klines(symbol="BTCUSDT", interval="1d", limit=1000), columns=column_names)
    kls["Close price"] = pd.to_numeric(kls["Close price"])
    kls["Open price"] = pd.to_numeric(kls["Open price"])
    kls["Open time"] = pd.to_datetime(kls["Open time"], unit="ms")
    ikls = kls.set_index("Open time")
    candlestick = go.Candlestick(x=ikls.index, open=ikls["Open price"], high=ikls["High price"], low=ikls["Low price"],
                                 close=ikls["Close price"], line={"width": 1})
    fig = go.Figure(data=[candlestick])
    fig.update_layout(width=800, height=600, title="BTCUSDT", yaxis_title="Price")
    fig.show()


if __name__ == "__main__":
    try:
        traceback.install(width=200, show_locals=True)
        print_curve()
    except KeyboardInterrupt:
        print("[bold]Stopped by user.")
        sys.exit(0)
