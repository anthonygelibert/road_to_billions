#!/usr/bin/env python3.12

"""Wayne script."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

import click
from click import FloatRange, IntRange
from rich import print, traceback  # noqa:A004
from rich.console import Console
from rich.progress import track
from rich.table import Table

from bin import Client
from strategy import Wayne

API_SECRET: Final[str | None] = os.environ.get("API_SECRET")
API_KEY: Final[str | None] = os.environ.get("API_KEY")


@click.group()
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose mode")
def wayne(*, verbose: bool) -> None:
    """Wayne."""
    traceback.install(width=200, show_locals=verbose)


@wayne.command(no_args_is_help=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("symbol")
@click.option("--capital", type=FloatRange(min_open=True, min=0.), default=1000., help="Initial capital")
@click.option("--limit", type=IntRange(min_open=True, min=0, max=1000), default=1000, help="Limit")
@click.option("--report", default=False, is_flag=True, help="Display the report")
@click.option("--curves", default=False, is_flag=True, help="Display the curves")
def earn_money(symbol: str, *, capital: float, limit: int, report: bool, curves: bool) -> None:
    """Run the analysis."""
    Wayne(symbol, capital=capital, limit=limit).earn_money(enable_report=report, enable_curves=curves)


@wayne.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--output-path", type=Path, default="assets/coin_info.json", help="Output path")
def download_coin_info(output_path: Path) -> None:
    """Download the coin information to update the “coin_info” JSON file."""
    Client(API_KEY, API_SECRET).save_coin_info(output_path)


@wayne.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_path", type=click.Path(path_type=Path, exists=True))
@click.option("--capital", type=FloatRange(min_open=True, min=0.), default=1000., help="Initial capital")
@click.option("--limit", type=IntRange(min_open=True, min=0, max=1000), default=1000, help="Limit")
def evaluate_symbols_offline(input_path: Path, *, capital: float, limit: int) -> None:
    """Look for symbols to invest in."""
    coin_info = Client(API_KEY, API_SECRET).coin_info(from_fake=input_path)

    results = [Wayne(ci.symbol, capital=capital, limit=limit).earn_money() for ci in
               track(coin_info, description="Evaluating symbols…")]
    best_results = sorted(results, reverse=True)[:5]

    table = Table(title=f"Evaluate {len(results)} symbols", title_style="bold red")
    table.add_column(justify="right", style="bold cyan")
    table.add_column("Profit")
    for result in best_results:
        table.add_row(result.symbol, f"{result.profit:.2f} USD")
    Console().print(table)


if __name__ == "__main__":
    try:
        wayne()
    except KeyboardInterrupt:
        print("[bold]Stopped by user.")
