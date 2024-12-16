#!/usr/bin/env python3.12

"""Wayne script."""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
from binance.spot import Spot as Client
from plotly.subplots import make_subplots
from rich import print, traceback  # noqa:A004
from rich.console import Console
from rich.table import Table
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator

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
    ema_indicator = EMAIndicator(close=data["Close price"], window=25)
    data["EMA25"] = ema_indicator.ema_indicator()
    # Relative Strength Index (RSI) over the close price: https://www.investopedia.com/terms/r/rsi.asp.
    rsi_indicator = RSIIndicator(close=data["Close price"], window=3)
    data["RSI3"] = rsi_indicator.rsi()
    # Took these values from a trading experimentation code:
    data["Buy"] = (data["Close price"] > data["EMA25"]) & (data["RSI3"] > 82)
    data["Sell"] = (data["RSI3"] < 20)
    return data


def _simulate_invest_strategy(data: pd.DataFrame, *, capital_start: float = 1000., stop_loss_pct: float = .032,
                              trailing_stop_pct: float = .001) -> None:
    """Simulate an invest strategy."""
    capital = capital_start
    peak = capital
    positions = 0.
    drawdown = 0.
    entry_price = 0.
    capital_curve = []
    stop_loss = 0.
    trailing_stop = 0.

    for _, row in data.iterrows():
        if positions == 0:
            if row["Buy"]:
                entry_price = row["Close price"]
                positions = capital / entry_price
                capital = 0.
                stop_loss = entry_price * (1. - stop_loss_pct)
                trailing_stop = entry_price * (1. + trailing_stop_pct)
        elif row["High price"] > trailing_stop:
            entry_price = row["High price"]
            stop_loss = entry_price * (1. - stop_loss_pct)
        elif row["Low price"] < stop_loss:
            capital = positions * stop_loss
            positions = 0.
        elif row["Sell"]:
            capital = positions * row["Close price"]
            positions = 0.

        # Calcul du drawdown
        current_value = positions * row["Close price"] if positions > 0. else capital
        if current_value > peak:
            peak = current_value
        else:
            current_drawdown = (peak - current_value) / peak
            drawdown = max(current_drawdown, drawdown)
        capital_curve.append(current_value)

    # Calcul du capital final et du profit
    capital_end = capital if positions == 0. else positions * data.iloc[-1]["Close price"]
    profit = capital_end - capital_start
    profit_percentage = (profit / capital_start) * 100.

    capital_structure = "liquidity" if positions == 0. else f"{positions:.2f} x {data.iloc[-1]['Close price']}"
    table = Table(title="Report", title_style="bold red", show_header=False)
    table.add_column(justify="right", style="bold cyan")
    table.add_row("Capital initial", f"{capital_start:.2f} USDT")
    table.add_row("Capital final", f"{capital_end:.2f} USDT ({capital_structure})")
    table.add_row("Profit", f"{profit:.2f} USDT")
    table.add_row("Rentabilité", f"{profit_percentage:.2f}%")
    table.add_row("Drawdown maximal", f"{drawdown * 100.:.2f}%")
    Console().print(table)

    data["Capital"] = capital_curve


def _print_the_curves(data: pd.DataFrame) -> None:
    """Display BTC2USD curve."""
    candlestick = go.Candlestick(x=data.index, open=data["Open price"], high=data["High price"], low=data["Low price"],
                                 close=data["Close price"], name="Stock")
    ema25 = go.Scatter(x=data.index, y=data["EMA25"], line={"color": "blue"}, mode="lines", name="EMA25")
    rsi3 = go.Scatter(x=data.index, y=data["RSI3"], mode="lines", name="RSI3")
    buy = go.Scatter(x=data.index, y=data["Buy"], mode="lines", line={"color": "green"}, name="Buy")
    sell = go.Scatter(x=data.index, y=data["Sell"], mode="lines", line={"color": "red"}, name="Sell")
    capital = go.Scatter(x=data.index, y=data["Capital"], mode="lines", name="Capital")

    fig = make_subplots(rows=4, shared_xaxes=True,
                        subplot_titles=("BTC 2 USD + EMA 25", "RSI 3", "Buy/Sell orders", "Capital"))
    fig.update_xaxes(rangeslider_visible=False)
    fig.add_trace(candlestick, 1, 1)
    fig.add_trace(ema25, 1, 1)
    fig.add_trace(rsi3, 2, 1)
    fig.add_trace(buy, 3, 1)
    fig.add_trace(sell, 3, 1)
    fig.add_trace(capital, 4, 1)

    fig.update_layout(width=800, height=600)
    fig.show()


if __name__ == "__main__":
    try:
        traceback.install(width=200, show_locals=True)
        raw_data = _generate_buy_sell_orders(_get_data("BTCUSDT"))
        _simulate_invest_strategy(raw_data)
        _print_the_curves(raw_data)
    except KeyboardInterrupt:
        print("[bold]Stopped by user.")
        sys.exit(0)
