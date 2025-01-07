"""All implemented strategies."""

from abc import ABC, abstractmethod
from typing import Any, override, Unpack

import pandas as pd
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
