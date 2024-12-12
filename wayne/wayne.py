#!/usr/bin/env python3.12

"""Wayne script."""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
from binance.spot import Spot as Client
from plotly.subplots import make_subplots
from rich import print, traceback  # noqa:A004
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

assert "API_KEY" in os.environ, "Please add API_KEY environment variable"
assert "API_SECRET" in os.environ, "Please add API_SECRET environment variable"


# noinspection PyArgumentList,PyUnresolvedReferences
def _get_data(symbol: str) -> pd.DataFrame:
    """Get the raw data for a symbol."""
    client = Client(os.environ["API_KEY"], os.environ["API_SECRET"])
    column_names = ["Open time", "Open price", "High price", "Low price", "Close price", "Volume", "Kline close time",
                    "Quote asset volume", "Number of trades", "Taker buy base asset volume",
                    "Taker buy quote asset volume", "Ignore"]
    kls = pd.DataFrame(client.ui_klines(symbol=symbol, interval="1d", limit=200), columns=column_names)
    kls["Close price"] = pd.to_numeric(kls["Close price"])
    kls["Open price"] = pd.to_numeric(kls["Open price"])
    kls["Open time"] = pd.to_datetime(kls["Open time"], unit="ms")
    return kls.set_index("Open time")


def print_curve() -> None:
    """Display BTC2USD curve."""
    data = _get_data("BTCUSDT")
    # Exponential Moving Average (EMA) over the close price.
    ema_indicator = EMAIndicator(close=data["Close price"], window=25)
    data["EMA25"] = ema_indicator.ema_indicator()
    # Relative Strength Index (RSI) over the close price: https://www.investopedia.com/terms/r/rsi.asp.
    rsi_indicator = RSIIndicator(close=data["Close price"], window=3)
    data["RSI3"] = rsi_indicator.rsi()
    # Took these values from a trading experimentation code:
    data["Buy"] = (data["Close price"] > data["EMA25"]) & (data["RSI3"] > 82)
    data["Sell"] = (data["RSI3"] < 20)

    candlestick = go.Candlestick(x=data.index, open=data["Open price"], high=data["High price"], low=data["Low price"],
                                 close=data["Close price"])
    ema25 = go.Scatter(x=data.index, y=data["EMA25"], line={"color": "blue"}, mode="lines")
    rsi3 = go.Scatter(x=data.index, y=data["RSI3"], mode="lines")
    buy = go.Scatter(x=data.index, y=data["Buy"], mode="lines", line={"color": "green"})
    sell = go.Scatter(x=data.index, y=data["Sell"], mode="lines", line={"color": "red"})

    fig = make_subplots(rows=3, shared_xaxes=True,
                        subplot_titles=("BTC 2 USD + EMA 25", "RSI 3", "Buy (green)/Sell (red) orders"))
    fig.add_trace(candlestick, 1, 1)
    fig.add_trace(ema25, 1, 1)
    fig.add_trace(rsi3, 2, 1)
    fig.add_trace(buy, 3, 1)
    fig.add_trace(sell, 3, 1)

    fig.update_layout(width=800, height=600)
    fig.show()


if __name__ == "__main__":
    try:
        traceback.install(width=200, show_locals=True)
        print_curve()
    except KeyboardInterrupt:
        print("[bold]Stopped by user.")
        sys.exit(0)
