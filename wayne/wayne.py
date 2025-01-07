#!/usr/bin/env python3.12

"""Wayne script."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

import click
from binance.spot import Spot as Client
from click import FloatRange, IntRange
from rich import print, traceback  # noqa:A004
from rich.console import Console
from rich.progress import track
from rich.table import Table

from models import CoinInfo
from strategy import Wayne

if TYPE_CHECKING:
    from models import InvestResult

assert "API_KEY" in os.environ, "Please add API_KEY environment variable"
assert "API_SECRET" in os.environ, "Please add API_SECRET environment variable"


@click.group()
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose mode")
def wayne(*, verbose: bool) -> None:
    """Wayne."""
    traceback.install(width=200, show_locals=verbose)


@wayne.command(no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("symbol")
@click.option("--capital", type=FloatRange(min_open=True, min=0.), default=1000., help="Initial capital")
@click.option("--interval", default="1d", help="Interval")
@click.option("--limit", type=IntRange(min_open=True, min=0, max=1000), default=1000, help="Limit")
@click.option("--report", default=False, is_flag=True, help="Display the report")
@click.option("--curves", default=False, is_flag=True, help="Display the curves")
def earn_money(symbol: str, *, capital: float, limit: int, interval: str, report: bool,  # noqa:PLR0913
               curves: bool) -> None:
    """Run the analysis."""
    Wayne(symbol, capital=capital, limit=limit, interval=interval).earn_money(enable_report=report,
                                                                              enable_curves=curves)


@wayne.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--output-path", type=Path, default="assets/coin_info.json", help="Output path")
def download_coin_info(output_path: Path) -> None:
    """Download the coin information to update the “coin_info” JSON file."""
    client = Client(os.environ["API_KEY"], os.environ["API_SECRET"])
    # noinspection PyArgumentList
    output_path.write_text(json.dumps(client.coin_info()), encoding="utf-8")


@wayne.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_path", type=click.Path(path_type=Path, exists=True))
@click.option("--capital", type=FloatRange(min_open=True, min=0.), default=1000., help="Initial capital")
@click.option("--interval", default="1d", help="Interval")
@click.option("--limit", type=IntRange(min_open=True, min=0, max=1000), default=1000, help="Limit")
def evaluate_symbols_offline(input_path: Path, *, capital: float, interval: str, limit: int) -> None:
    """Look for symbols to invest in."""
    coins_info = json.loads(input_path.read_text(encoding="utf-8"))
    results: list[tuple[str, InvestResult]] = []
    for raw_coin_info in track(coins_info, description="Evaluating symbols…"):
        coin_info = CoinInfo.model_validate(raw_coin_info)
        coin_name = f"{coin_info.coin}USDT"
        if not coin_info.is_legal_money and coin_info.trading and coin_info.coin != "USDT":
            w = Wayne(coin_name, capital=capital, limit=limit, interval=interval)
            results.append((coin_name, w.earn_money(enable_report=False, enable_curves=False)))

    results.sort(key=lambda result: result[1].profit, reverse=True)

    table = Table(title=f"Evaluate symbols {len(results)}/{len(coins_info)}", title_style="bold red", show_header=False)
    table.add_column(justify="right", style="bold cyan")
    table.add_column()
    for res in results[:5]:
        table.add_row(res[0], f"{res[1].profit:.2f} USD")
    Console().print(table)


if __name__ == "__main__":
    try:
        wayne()
    except KeyboardInterrupt:
        print("[bold]Stopped by user.")
