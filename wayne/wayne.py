#!/usr/bin/env python3.12

"""Wayne script."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import click
import pandas as pd
import plotly.graph_objects as go
from binance.spot import Spot as Client
from plotly.subplots import make_subplots
from rich import print, traceback  # noqa:A004
from rich.console import Console
from rich.table import Table

from strategy import EMARSIBuyOrderGenerator, MACDBuyOrderGenerator, TrailingStopStrategy

if TYPE_CHECKING:
    from models import InvestResult

assert "API_KEY" in os.environ, "Please add API_KEY environment variable"
assert "API_SECRET" in os.environ, "Please add API_SECRET environment variable"


class Wayne:
    """Call me Bruce."""

    def __init__(self, symbol: str, *, interval: str = "1d", limit: int = 1000) -> None:
        self._symbol = symbol
        self._limit = limit
        self._interval = interval
        self._raw_data = self._get_data()

    def earn_money(self, *, enable_curves: bool) -> None:
        """Run the analysis."""
        order_generator_ema_rsi = EMARSIBuyOrderGenerator(self._raw_data)
        completed_data_ema_rsi = order_generator_ema_rsi.generate(ema_window=25, rsi_window=3, rsi_threshold=82)

        order_generator_macd = MACDBuyOrderGenerator(self._raw_data)
        completed_data_macd = order_generator_macd.generate()

        tss_ema_rsi = TrailingStopStrategy(completed_data_ema_rsi, capital=1000.)
        tss_macd = TrailingStopStrategy(completed_data_macd, capital=1000.)
        results = {"EMA25 + RSI3>82 + !Secure": tss_ema_rsi.apply(secure=False, stop_loss_pct=.032,
                                                                  trailing_stop_pct=.001),
                   "EMA25 + RSI3>82 + Secure": tss_ema_rsi.apply(secure=True, stop_loss_pct=.032,
                                                                 trailing_stop_pct=.001),
                   "MACD": tss_macd.apply(secure=False, stop_loss_pct=.032, trailing_stop_pct=.001)}

        self._print_report(results)
        if enable_curves:
            self._print_curves(completed_data_ema_rsi, buy_order_strategy, results)

    def _get_data(self) -> pd.DataFrame:
        """Get the raw data for a symbol."""
        client = Client(os.environ["API_KEY"], os.environ["API_SECRET"])
        column_names = ["Open time", "Open price", "High price", "Low price", "Close price", "Volume",
                        "Kline close time", "Quote asset volume", "Number of trades", "Taker buy base asset volume",
                        "Taker buy quote asset volume", "Ignore"]
        # noinspection PyArgumentList
        kls = pd.DataFrame(client.ui_klines(symbol=self._symbol, interval=self._interval, limit=self._limit),
                           columns=column_names)
        kls["Close price"] = pd.to_numeric(kls["Close price"])
        kls["Open price"] = pd.to_numeric(kls["Open price"])
        kls["High price"] = pd.to_numeric(kls["High price"])
        kls["Low price"] = pd.to_numeric(kls["Low price"])
        kls["Open time"] = pd.to_datetime(kls["Open time"], unit="ms")
        return kls.set_index("Open time")

    def _print_report(self, results: dict[str, InvestResult]) -> None:
        table = Table(title=f"Trailing Stop on {self._symbol}", title_style="bold red")
        table.add_column(justify="right", style="bold cyan")
        for name in results:
            table.add_column(name)

        table.add_row("Capital initial", *[f"{res.capital_start:.2f} USD" for res in results.values()])
        table.add_row("Duration", *[f"{self._limit} x {self._interval}"] * len(results))
        table.add_section()
        table.add_row("Capital final",
                      *[f"{res.capital_end:.2f} USD ({res.capital_structure})" for res in results.values()])
        table.add_row("Profit", *[f"{res.profit:.2f} USD" for res in results.values()])
        table.add_row("Rentabilité", *[f"{res.profit_percentage:.2f}%" for res in results.values()])
        table.add_row("Drawdown maximal", *[f"{res.drawdown * 100.:.2f}%" for res in results.values()])
        table.add_row("Frais de plateforme", *[f"{res.platform_fees:.2f} USD" for res in results.values()])
        table.add_section()
        table.add_row("Min", *[f"{res.min:.2f} USD" for res in results.values()])
        table.add_row("Max", *[f"{res.max:.2f} USD" for res in results.values()])
        Console().print(table)

    def _print_curves(self, data: pd.DataFrame, results: dict[str, InvestResult]) -> None:
        """Display BTC2USD curve."""
        candlestick = go.Candlestick(x=data.index, open=data["Open price"], high=data["High price"],
                                     low=data["Low price"], close=data["Close price"], name="Stock")
        ema = go.Scatter(x=data.index, y=data["EMA"], line={"color": "blue"}, mode="lines", name="EMA")

        fig = make_subplots(rows=1 + len(results), shared_xaxes=True,
                            subplot_titles=(f"{self._symbol}", *[f"Capital ({name})" for name in results]))
        fig.add_trace(candlestick, 1, 1)
        fig.update_xaxes(rangeslider_visible=False)
        fig.add_trace(ema, 1, 1)

        for i, (name, res) in enumerate(results.items(), start=2):
            curve = go.Scatter(x=data.index, y=res.capital_curve, mode="lines", name=f"Capital ({name})",
                               line={"color": "green"})
            fig.add_trace(curve, i, 1)

        fig.update_layout(width=800, height=600)
        fig.show()


@click.command()
@click.option("--symbol", default="BTCUSDT", help="Symbol to analyze")
@click.option("--curves", default=False, is_flag=True, help="Display the curves")
def wayne(symbol: str, *, curves: bool) -> None:
    """Wayne."""
    traceback.install(width=200, show_locals=True)
    Wayne(symbol).earn_money(enable_curves=curves)


if __name__ == "__main__":
    try:
        wayne()
    except KeyboardInterrupt:
        print("[bold]Stopped by user.")
