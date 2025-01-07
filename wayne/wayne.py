#!/usr/bin/env python3.12

"""Wayne script."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import click
import pandas as pd
import plotly.graph_objects as go
from binance.spot import Spot as Client
from plotly.subplots import make_subplots
from rich import print, traceback  # noqa:A004
from rich.console import Console
from rich.progress import track
from rich.table import Table

from models import CoinInfo
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

    def earn_money(self, *, enable_report: bool, enable_curves: bool) -> InvestResult:
        """Run the analysis."""
        order_generator_ema_rsi = EMARSIBuyOrderGenerator(self._raw_data)
        completed_data_ema_rsi = order_generator_ema_rsi.generate(ema_window=25, rsi_window=3, rsi_threshold=82)

        order_generator_macd = MACDBuyOrderGenerator(self._raw_data)
        completed_data_macd = order_generator_macd.generate()

        tss_ema_rsi = TrailingStopStrategy(completed_data_ema_rsi, capital=1000.)
        tss_macd = TrailingStopStrategy(completed_data_macd, capital=1000.)
        results = {"EMA/RSI3": tss_ema_rsi.apply(stop_loss_pct=.032, trailing_stop_pct=.001),
                   "MACD": tss_macd.apply(stop_loss_pct=.032, trailing_stop_pct=.001)}

        if enable_report:
            self._print_report(results)
        if enable_curves:
            self._print_curves(completed_data_ema_rsi, results)

        return results["MACD"]

    def _get_data(self) -> pd.DataFrame:
        """Get the raw data for a symbol."""
        client = Client(os.environ["API_KEY"], os.environ["API_SECRET"])
        column_names = ["Open time", "Open price", "High price", "Low price", "Close price", "Volume",
                        "Kline close time", "Quote asset volume", "Number of trades", "Taker buy base asset volume",
                        "Taker buy quote asset volume", "Ignore"]
        # noinspection PyArgumentList
        kls = pd.DataFrame(client.ui_klines(symbol=self._symbol, interval=self._interval, limit=self._limit),
                           columns=column_names)
        kls["Open time"] = pd.to_datetime(kls["Open time"], unit="ms")
        kls["Open price"] = pd.to_numeric(kls["Open price"])
        kls["High price"] = pd.to_numeric(kls["High price"])
        kls["Low price"] = pd.to_numeric(kls["Low price"])
        kls["Close price"] = pd.to_numeric(kls["Close price"])
        kls["Volume"] = pd.to_numeric(kls["Volume"])
        kls["Kline close time"] = pd.to_datetime(kls["Kline close time"], unit="ms")
        kls["Quote asset volume"] = pd.to_numeric(kls["Quote asset volume"])
        kls["Number of trades"] = pd.to_numeric(kls["Number of trades"])
        kls["Taker buy base asset volume"] = pd.to_numeric(kls["Taker buy base asset volume"])
        kls["Taker buy quote asset volume"] = pd.to_numeric(kls["Taker buy quote asset volume"])
        return kls.set_index("Open time")

    def _print_report(self, results: dict[str, InvestResult]) -> None:
        table = Table(title=f"Trailing Stop on {self._symbol}", title_style="bold red")
        table.add_column(justify="right", style="bold cyan")
        for name in results:
            table.add_column(name)

        table.add_row("Capital initial", *[f"{res.capital_start:.0f} USD" for res in results.values()])
        table.add_row("Duration", *[f"{self._limit} x {self._interval}"] * len(results))
        table.add_section()
        table.add_row("Capital final",
                      *[f"{res.capital_end:.2f} USD\n ↳ {res.capital_structure}" for res in results.values()])
        table.add_row("Profit", *[f"{res.profit:.2f} USD" for res in results.values()])
        table.add_row("Rentabilité", *[f"{res.profit_percentage:.2f}%" for res in results.values()])
        table.add_row("Drawdown maximal", *[f"{res.drawdown * 100.:.2f}%" for res in results.values()])
        table.add_row("Frais de plateforme", *[f"{res.platform_fees:.2f} USD" for res in results.values()])
        table.add_section()
        table.add_row("Capital minimal", *[f"{res.min:.2f} USD" for res in results.values()])
        table.add_row("Capital maximal", *[f"{res.max:.2f} USD" for res in results.values()])
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


def download_coin_info() -> None:
    """Download the coin information to update the “coin_info” JSON file."""
    client = Client(os.environ["API_KEY"], os.environ["API_SECRET"])
    # noinspection PyArgumentList
    Path("assets/coin_info.json").write_text(json.dumps(client.coin_info()), encoding="utf-8")


def evaluate_symbols() -> None:
    """Look for symbols to invest in."""
    coins_info = json.loads(Path("assets/coin_info.json").read_text(encoding="utf-8"))
    results: list[tuple[str, InvestResult]] = []
    for raw_coin_info in track(coins_info, description="Evaluating symbols…"):
        coin_info = CoinInfo.model_validate(raw_coin_info)
        coin_name = f"{coin_info.coin}USDT"
        if not coin_info.is_legal_money and coin_info.trading and coin_info.coin != "USDT":
            results.append((coin_name, Wayne(coin_name).earn_money(enable_report=False, enable_curves=False)))

    results.sort(key=lambda result: result[1].profit, reverse=True)

    table = Table(title=f"Evaluate symbols {len(results)}/{len(coins_info)}", title_style="bold red", show_header=False)
    table.add_column(justify="right", style="bold cyan")
    table.add_column()
    for res in results[:5]:
        table.add_row(res[0], f"{res[1].profit:.2f} USD")
    Console().print(table)


@click.command()
@click.option("--symbol", default="BTCUSDT", help="Symbol to analyze")
@click.option("--report", default=False, is_flag=True, help="Display the report")
@click.option("--curves", default=False, is_flag=True, help="Display the curves")
def wayne(symbol: str, *, report: bool, curves: bool) -> None:
    """Wayne."""
    traceback.install(width=200, show_locals=True)
    Wayne(symbol).earn_money(enable_report=report, enable_curves=curves)  # download_coin_info()  # evaluate_symbols()


if __name__ == "__main__":
    try:
        wayne()
    except KeyboardInterrupt:
        print("[bold]Stopped by user.")
