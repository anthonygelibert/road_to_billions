#!/usr/bin/env python3.12

"""Wayne script."""

from __future__ import annotations

import os

import click
import pandas as pd
import plotly.graph_objects as go
from binance.spot import Spot as Client
from plotly.subplots import make_subplots
from rich import print, traceback  # noqa:A004
from rich.console import Console
from rich.table import Table
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

from strategy import TrailingStopStrategy

assert "API_KEY" in os.environ, "Please add API_KEY environment variable"
assert "API_SECRET" in os.environ, "Please add API_SECRET environment variable"


def _get_data(symbol: str, *, interval: str = "1d", limit: int = 1000) -> pd.DataFrame:
    """Get the raw data for a symbol."""
    client = Client(os.environ["API_KEY"], os.environ["API_SECRET"])
    column_names = ["Open time", "Open price", "High price", "Low price", "Close price", "Volume", "Kline close time",
                    "Quote asset volume", "Number of trades", "Taker buy base asset volume",
                    "Taker buy quote asset volume", "Ignore"]
    # noinspection PyArgumentList
    kls = pd.DataFrame(client.ui_klines(symbol=symbol, interval=interval, limit=limit), columns=column_names)
    kls["Close price"] = pd.to_numeric(kls["Close price"])
    kls["Open price"] = pd.to_numeric(kls["Open price"])
    kls["High price"] = pd.to_numeric(kls["High price"])
    kls["Low price"] = pd.to_numeric(kls["Low price"])
    kls["Open time"] = pd.to_datetime(kls["Open time"], unit="ms")
    return kls.set_index("Open time")


def _generate_buy_sell_orders(data: pd.DataFrame) -> pd.DataFrame:
    """Generate “buy” and “sell” orders."""
    # Exponential Moving Average (EMA) over the close price.
    data["EMA25"] = EMAIndicator(close=data["Close price"], window=25).ema_indicator()
    # Relative Strength Index (RSI) over the close price: https://www.investopedia.com/terms/r/rsi.asp.
    data["RSI3"] = RSIIndicator(close=data["Close price"], window=3).rsi()
    # Took these values from a trading experimentation code:
    data["Buy"] = (data["Close price"] > data["EMA25"]) & (data["RSI3"] > 82)
    return data


def _trailing_stop_invest_strategies(data: pd.DataFrame, *, capital_start: float = 1000.) -> None:
    tss = TrailingStopStrategy(data, capital=capital_start)
    not_secure = tss.apply(secure=False, stop_loss_pct=.032, trailing_stop_pct=.001)
    secure = tss.apply(secure=True, stop_loss_pct=.032, trailing_stop_pct=.001)

    table = Table(title="Report “Trailing Stop” on BTCUSDT", title_style="bold red")
    table.add_column(justify="right", style="bold cyan")
    table.add_column("Secure == False")
    table.add_column("Secure == True")
    table.add_row("Capital initial", f"{not_secure.capital_start:.2f} USDT", f"{secure.capital_start:.2f} USDT")
    table.add_row("Capital final", f"{not_secure.capital_end:.2f} USDT ({not_secure.capital_structure})",
                  f"{secure.capital_end:.2f} USDT ({secure.capital_structure})")
    table.add_row("Profit", f"{not_secure.profit:.2f} USDT", f"{secure.profit:.2f} USDT")
    table.add_row("Rentabilité", f"{not_secure.profit_percentage:.2f}%", f"{secure.profit_percentage:.2f}%")
    table.add_row("Drawdown maximal", f"{not_secure.drawdown * 100.:.2f}%", f"{secure.drawdown * 100.:.2f}%")
    table.add_row("Max", f"{not_secure.max:.2f} USDT", f"{secure.max:.2f} USDT")
    table.add_row("Min", f"{not_secure.min:.2f} USDT", f"{secure.min:.2f} USDT")

    Console().print(table)

    data["Capital Not Secure"] = not_secure.capital_curve
    data["Capital Secure"] = secure.capital_curve


def _print_the_curves(data: pd.DataFrame) -> None:
    """Display BTC2USD curve."""
    candlestick = go.Candlestick(x=data.index, open=data["Open price"], high=data["High price"], low=data["Low price"],
                                 close=data["Close price"], name="Stock")
    ema25 = go.Scatter(x=data.index, y=data["EMA25"], line={"color": "blue"}, mode="lines", name="EMA25")
    capital_not_secure = go.Scatter(x=data.index, y=data["Capital Not Secure"], mode="lines",
                                    name="Capital (Secure=False)")
    capital_secure = go.Scatter(x=data.index, y=data["Capital Secure"], mode="lines", name="Capital (Secure=True)")

    fig = make_subplots(rows=3, shared_xaxes=True,
                        subplot_titles=("BTC 2 USD + EMA 25", "Capital (Secure=False)", "Capital (Secure=True)"))
    fig.add_trace(candlestick, 1, 1)
    fig.update_xaxes(rangeslider_visible=False)
    fig.add_trace(ema25, 1, 1)
    fig.add_trace(capital_not_secure, 2, 1)
    fig.add_trace(capital_secure, 3, 1)

    fig.update_layout(width=800, height=600)
    fig.show()


@click.command()
@click.option("--symbol", default="BTCUSDT", help="Symbol to analyze")
@click.option("--curves", default=False, is_flag=True, help="Display the curves")
def wayne(symbol: str, *, curves: bool) -> None:
    """Wayne."""
    traceback.install(width=200, show_locals=True)
    raw_data = _generate_buy_sell_orders(_get_data(symbol))
    _trailing_stop_invest_strategies(raw_data)
    if curves:
        _print_the_curves(raw_data)


if __name__ == "__main__":
    try:
        wayne()
    except KeyboardInterrupt:
        print("[bold]Stopped by user.")
