"""All implemented strategies."""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Any, override, Unpack

import pandas as pd
from binance.spot import Spot as Client
from plotly import graph_objects as go
from plotly.subplots import make_subplots
from rich.console import Console
from rich.table import Table
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

from models import EMARSIBuyOrderGeneratorParameters, InvestResult, TrailingStopParameters


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
        new_data["Buy"] = (new_data["Close price"] > new_data["EMA"]) & (new_data["RSI"] > kwargs["rsi_threshold"])
        return new_data


class MACDBuyOrderGenerator(BuyOrderGenerator):
    """Buy order generator based on the MACD."""

    @override
    def generate(self) -> pd.DataFrame:
        """Generate “buy” orders using the MACD."""
        new_data = self._data.copy()
        new_data["Buy"] = MACD(close=new_data["Close price"]).macd_diff() > 0
        return new_data


class Strategy(ABC):
    """Abstract strategy."""

    def __init__(self, data: pd.DataFrame, *, capital: float) -> None:
        self._capital_start = capital
        self._data = data

    @abstractmethod
    def apply(self, **kwargs: dict[str, Any]) -> InvestResult:
        """Apply the strategy."""


class TrailingStopStrategy(Strategy):
    """Strategy based on a trailing stop."""

    @override
    def apply(self, **kwargs: Unpack[TrailingStopParameters]) -> InvestResult:
        current_capital = capital = self._capital_start
        capital_curve: list[float] = []

        platform_fees = 0.
        peak = capital
        positions = 0.
        drawdown = 0.

        stop_loss = 0.
        trailing_stop = 0.

        for _, row in self._data.iterrows():
            if positions == 0.:
                if row["Buy"] and capital > 0.:
                    entry_price = row["Close price"]
                    positions = (capital / entry_price)
                    # https://www.binance.com/fr/support/faq/e85d6e703b874674840122196b89780a
                    platform_fees += positions * entry_price * 0.001  # 1‰ fee.
                    positions *= 0.999  # 1‰ fee.
                    capital = 0.
                    stop_loss = entry_price * (1. - kwargs["stop_loss_pct"])
                    trailing_stop = entry_price * (1. + kwargs["trailing_stop_pct"])
            elif row["High price"] > trailing_stop:
                entry_price = row["High price"]
                stop_loss = entry_price * (1. - kwargs["stop_loss_pct"])
                trailing_stop = entry_price * (1. + kwargs["trailing_stop_pct"])
            elif row["Low price"] < stop_loss:
                capital = (positions * stop_loss)
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

        for _, row in self._data.iterrows():
            if positions == 0.:
                if row["Buy"] and capital > 0.:
                    entry_price = row["Close price"]
                    positions = (capital / entry_price)
                    # https://www.binance.com/fr/support/faq/e85d6e703b874674840122196b89780a
                    platform_fees += positions * entry_price * 0.001  # 1‰ fee.
                    positions *= 0.999  # 1‰ fee.
                    capital = 0.
            elif not row["Buy"]:
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

        entry_price = self._data.iloc[0]["Close price"]
        positions = (capital / entry_price)
        # https://www.binance.com/fr/support/faq/e85d6e703b874674840122196b89780a
        platform_fees += positions * entry_price * 0.001  # 1‰ fee.
        positions *= 0.999  # 1‰ fee.

        for _, row in self._data.iterrows():
            current_capital = positions * row["Close price"]
            peak = max(current_capital, peak)
            current_drawdown = (peak - current_capital) / peak
            drawdown = max(current_drawdown, drawdown)
            capital_curve.append(current_capital)

        output_price = self._data.iloc[-1]["Close price"]
        capital = (positions * output_price)
        # https://www.binance.com/fr/support/faq/e85d6e703b874674840122196b89780a
        platform_fees += capital * 0.001  # 1‰ fee.
        capital *= 0.999  # 1‰ fee.

        return InvestResult(capital_start=self._capital_start, capital_end=capital, drawdown=drawdown,
                            capital_curve=capital_curve, positions_end=positions, platform_fees=platform_fees)


class Wayne:
    """Call me Bruce."""

    def __init__(self, symbol: str, *, capital: float, interval: str = "1d", limit: int = 1000) -> None:
        self._symbol = symbol
        self._capital = capital
        self._limit = limit
        self._interval = interval
        self._data_day, self._data_hour = self._get_data()

    def earn_money(self, *, enable_report: bool, enable_curves: bool) -> InvestResult:
        """Run the analysis."""
        order_generator_ema_rsi = EMARSIBuyOrderGenerator(self._data_day)
        completed_data_ema_rsi = order_generator_ema_rsi.generate(ema_window=25, rsi_window=3, rsi_threshold=82)

        order_generator_macd = MACDBuyOrderGenerator(self._data_day)
        completed_data_macd = order_generator_macd.generate()

        tss_ema_rsi = TrailingStopStrategy(completed_data_ema_rsi, capital=self._capital)
        tss_macd = SimpleStrategy(completed_data_macd, capital=self._capital)
        no_strat = NoStrategy(completed_data_macd, capital=self._capital)
        results = {"EMA/RSI3": tss_ema_rsi.apply(stop_loss_pct=.032, trailing_stop_pct=.001), "MACD": tss_macd.apply(),
                   "No strat": no_strat.apply()}

        if enable_report:
            self._print_report(results)
        if enable_curves:
            self._print_curves(completed_data_ema_rsi, results)

        return results["MACD"]

    def _get_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Get the raw data for a symbol."""

        def convert_dataframe(data: pd.DataFrame) -> pd.DataFrame:
            """Convert dataframe."""
            data["Open time"] = pd.to_datetime(data["Open time"], unit="ms")
            data["Open price"] = pd.to_numeric(data["Open price"])
            data["High price"] = pd.to_numeric(data["High price"])
            data["Low price"] = pd.to_numeric(data["Low price"])
            data["Close price"] = pd.to_numeric(data["Close price"])
            data["Volume"] = pd.to_numeric(data["Volume"])
            data["Kline close time"] = pd.to_datetime(data["Kline close time"], unit="ms")
            data["Quote asset volume"] = pd.to_numeric(data["Quote asset volume"])
            data["Number of trades"] = pd.to_numeric(data["Number of trades"])
            data["Taker buy base asset volume"] = pd.to_numeric(data["Taker buy base asset volume"])
            data["Taker buy quote asset volume"] = pd.to_numeric(data["Taker buy quote asset volume"])
            return data.set_index("Open time")

        client = Client(os.environ["API_KEY"], os.environ["API_SECRET"])
        column_names = ["Open time", "Open price", "High price", "Low price", "Close price", "Volume",
                        "Kline close time", "Quote asset volume", "Number of trades", "Taker buy base asset volume",
                        "Taker buy quote asset volume", "Ignore"]
        # noinspection PyArgumentList
        kls_day = pd.DataFrame(client.ui_klines(symbol=self._symbol, interval="1d", limit=1000), columns=column_names)
        oldest_time = kls_day.iloc[0]["Open time"]
        # noinspection PyArgumentList
        kls_hour = pd.DataFrame(client.ui_klines(symbol=self._symbol, interval="1h", limit=1000, startTime=oldest_time),
                                columns=column_names)

        while kls_day.iloc[-1]["Open time"] > kls_hour.iloc[-1]["Open time"]:
            next_start_time = kls_hour.iloc[-1]["Open time"] + 3600000
            # noinspection PyArgumentList
            next_data = pd.DataFrame(
                    client.ui_klines(symbol=self._symbol, interval="1h", limit=1000, startTime=next_start_time),
                    columns=column_names)
            kls_hour = pd.concat([kls_hour, next_data])
        return convert_dataframe(kls_day), convert_dataframe(kls_hour)

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
