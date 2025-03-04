"""All implemented strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, override, TYPE_CHECKING, Unpack

from plotly import graph_objects as go
from plotly.subplots import make_subplots
from rich.console import Console
from rich.table import Table
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

from bin import Client
from models import (EMARSIBuyOrderGeneratorParameters, InvestmentEvaluation, InvestResult,
                    MACDBuyOrderGeneratorParameters, TrailingStopParameters, )

if TYPE_CHECKING:
    import pandas as pd


class BuyOrderGenerator(ABC):
    """Abstract buy order generator."""

    def __init__(self, data: pd.DataFrame) -> None:
        self._data = data

    @abstractmethod
    def generate(self, **kwargs: dict[str, Any]) -> pd.DataFrame:
        """Generate buy orders."""


class EMARSIBuyOrderGenerator(BuyOrderGenerator):
    """Buy order generator based on the EMA and the RSI."""

    @override
    def generate(self, **kwargs: Unpack[EMARSIBuyOrderGeneratorParameters]) -> pd.DataFrame:
        """Generate “buy” orders using an EMA and the RSI."""
        new_data = self._data.copy()
        # Exponential Moving Average (EMA) over the close price.
        new_data["EMA"] = EMAIndicator(close=new_data["Close price"], window=kwargs["ema_window"]).ema_indicator()
        # Relative Strength Index (RSI) over the close price: https://www.investopedia.com/terms/r/rsi.asp.
        new_data["RSI"] = RSIIndicator(close=new_data["Close price"], window=kwargs["rsi_window"]).rsi()
        # Took these values from a trading experimentation code:
        new_data["Buy"] = (new_data["Close price"] > new_data["EMA"]) & (new_data["RSI"] > kwargs["rsi_buy_threshold"])
        new_data["Sell"] = (new_data["RSI"] < kwargs["rsi_sell_threshold"])
        return new_data


class MACDBuyOrderGenerator(BuyOrderGenerator):
    """Buy order generator based on the MACD."""

    @override
    def generate(self, **kwargs: Unpack[MACDBuyOrderGeneratorParameters]) -> pd.DataFrame:
        """Generate “buy” orders using the MACD."""
        new_data = self._data.copy()
        new_data["Buy"] = MACD(close=new_data["Close price"]).macd_diff() > kwargs["macd_buy_threshold"]
        new_data["Sell"] = MACD(close=new_data["Close price"]).macd_diff() < kwargs["macd_sell_threshold"]
        return new_data


class Strategy(ABC):
    """Abstract strategy."""

    def __init__(self, day_data, *, capital: float) -> None:
        self._capital_start = capital
        self._day_data = day_data

    @abstractmethod
    def apply(self, **kwargs: dict[str, Any]) -> InvestResult:
        """Apply the strategy."""


class TrailingStopStrategy(Strategy):
    """Strategy based on a trailing stop."""

    def __init__(self, day_data: pd.DataFrame, hour_data: pd.DataFrame, *, capital: float) -> None:
        super().__init__(day_data, capital=capital)
        self._hour_data = hour_data

    @override
    def apply(self, **kwargs: Unpack[TrailingStopParameters]) -> InvestResult:
        current_capital = capital = self._capital_start
        capital_curve: list[float] = []

        platform_fees = 0.
        peak = capital
        positions = 0.
        drawdown = 0.

        stop_loss = 0.

        day = 0
        for _, row in self._hour_data.iterrows():
            if positions != 0.:
                stop_loss = max(stop_loss, row["Close price"] * (1. - kwargs["stop_loss_pct"]))
                if row["Close price"] < stop_loss:
                    capital = positions * stop_loss
                    # https://www.binance.com/fr/support/faq/e85d6e703b874674840122196b89780a
                    platform_fees += capital * 0.001  # 1‰ fee.
                    capital *= 0.999  # 1‰ fee.
                    positions = 0.
            if day < len(self._day_data) and row.name == self._day_data.iloc[day].name:
                day_row = self._day_data.iloc[day]
                if positions == 0.:
                    if day_row["Buy"] and capital > 0.:
                        entry_price = day_row["Close price"]
                        positions = capital / entry_price
                        # https://www.binance.com/fr/support/faq/e85d6e703b874674840122196b89780a
                        platform_fees += positions * entry_price * 0.001  # 1‰ fee.
                        positions *= 0.999  # 1‰ fee.
                        capital = 0.
                        stop_loss = entry_price * (1. - kwargs["stop_loss_pct"])
                day += 1

                current_capital = capital if positions == 0. else positions * day_row["Close price"]
                peak = max(current_capital, peak)

                current_drawdown = (peak - current_capital) / peak

                drawdown = max(current_drawdown, drawdown)
                capital_curve.append(current_capital)

        return InvestResult(capital_start=self._capital_start, capital_end=current_capital, drawdown=0,
                            capital_curve=capital_curve, positions_end=positions, platform_fees=platform_fees)


class SimpleStrategy(Strategy):
    """Strategy only based on buying order."""

    @override
    def apply(self) -> InvestResult:
        current_capital = capital = self._capital_start
        capital_curve: list[float] = []

        platform_fees = 0.
        peak = capital
        positions = 0.
        drawdown = 0.

        for _, row in self._day_data.iterrows():
            if positions == 0.:
                if row["Buy"] and capital > 0.:
                    entry_price = row["Close price"]
                    positions = (capital / entry_price)
                    # https://www.binance.com/fr/support/faq/e85d6e703b874674840122196b89780a
                    platform_fees += positions * entry_price * 0.001  # 1‰ fee.
                    positions *= 0.999  # 1‰ fee.
                    capital = 0.
            elif row["Sell"]:
                capital = (positions * row["Close price"])
                # https://www.binance.com/fr/support/faq/e85d6e703b874674840122196b89780a
                platform_fees += capital * 0.001  # 1‰ fee.
                capital *= 0.999  # 1‰ fee.
                positions = 0.

            current_capital = capital if positions == 0. else positions * row["Close price"]
            peak = max(current_capital, peak)
            current_drawdown = (peak - current_capital) / peak
            drawdown = max(current_drawdown, drawdown)
            capital_curve.append(current_capital)

        return InvestResult(capital_start=self._capital_start, capital_end=current_capital, drawdown=drawdown,
                            capital_curve=capital_curve, positions_end=positions, platform_fees=platform_fees)


class NoStrategy(Strategy):
    """No strategy."""

    @override
    def apply(self) -> InvestResult:
        capital = self._capital_start
        capital_curve: list[float] = []

        platform_fees = 0.
        peak = capital
        drawdown = 0.

        entry_price = self._day_data.iloc[0]["Close price"]
        positions = (capital / entry_price)
        # https://www.binance.com/fr/support/faq/e85d6e703b874674840122196b89780a
        platform_fees += positions * entry_price * 0.001  # 1‰ fee.
        positions *= 0.999  # 1‰ fee.

        for _, row in self._day_data.iterrows():
            current_capital = positions * row["Close price"]
            peak = max(current_capital, peak)
            current_drawdown = (peak - current_capital) / peak
            drawdown = max(current_drawdown, drawdown)
            capital_curve.append(current_capital)

        output_price = self._day_data.iloc[-1]["Close price"]
        capital = (positions * output_price)
        # https://www.binance.com/fr/support/faq/e85d6e703b874674840122196b89780a
        platform_fees += capital * 0.001  # 1‰ fee.
        capital *= 0.999  # 1‰ fee.

        return InvestResult(capital_start=self._capital_start, capital_end=capital, drawdown=drawdown,
                            capital_curve=capital_curve, positions_end=positions, platform_fees=platform_fees)


class Wayne:
    """Call me Bruce."""

    def __init__(self, symbol: str, *, capital: float, limit: int = 1000) -> None:
        self._symbol = symbol
        self._capital = capital
        self._limit = limit
        self._data_day, self._data_hour = Client().get_day_hour_data(symbol, limit=limit)

    def earn_money(self, *, enable_report: bool = False, enable_curves: bool = False) -> InvestmentEvaluation:
        """Run the analysis."""
        order_generator_ema_rsi = EMARSIBuyOrderGenerator(self._data_day)
        completed_data_ema_rsi = order_generator_ema_rsi.generate(ema_window=25, rsi_window=3, rsi_buy_threshold=82,
                                                                  rsi_sell_threshold=20)

        order_generator_macd = MACDBuyOrderGenerator(self._data_day)
        completed_data_macd = order_generator_macd.generate(macd_buy_threshold=0, macd_sell_threshold=-1)

        ts_strat_macd = TrailingStopStrategy(completed_data_ema_rsi, self._data_hour, capital=self._capital)
        simple_strat_macd = SimpleStrategy(completed_data_ema_rsi, capital=self._capital)
        no_strat = NoStrategy(completed_data_ema_rsi, capital=self._capital)
        results = {"TS strat": ts_strat_macd.apply(stop_loss_pct=0.2, trailing_stop_pct=.001),
                   "Simple strat": simple_strat_macd.apply(), "No strat": no_strat.apply()}

        if enable_report:
            self._print_report(results)
        if enable_curves:
            self._print_curves(completed_data_ema_rsi, results)

        return InvestmentEvaluation(symbol=self._symbol, result=results["TS strat"])

    def _print_report(self, results: dict[str, InvestResult]) -> None:
        table = Table(title=f"Trailing Stop on {self._symbol}", title_style="bold red")
        table.add_column(justify="right", style="bold cyan")
        for name in results:
            table.add_column(name)

        table.add_row("Capital initial", *[f"{res.capital_start:.0f} USD" for res in results.values()])
        table.add_row("Duration", *[f"{self._limit} x 1d"] * len(results))
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
