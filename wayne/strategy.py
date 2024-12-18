"""All implemented strategies."""

from abc import ABC, abstractmethod
from typing import Any, override, Unpack

import pandas as pd

from models import InvestResult, TrailingStopParameters


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

        peak = capital
        positions = 0.
        drawdown = 0.

        stop_loss = 0.
        trailing_stop = 0.

        for _, row in self._data.iterrows():
            if positions == 0.:
                if row["Buy"]:
                    entry_price = row["Close price"]
                    positions = capital / entry_price
                    capital = 0.
                    stop_loss = entry_price * (1. - kwargs["stop_loss_pct"])
                    trailing_stop = entry_price * (1. + kwargs["trailing_stop_pct"])
            elif row["High price"] > trailing_stop:
                entry_price = row["High price"]
                stop_loss = entry_price * (1. - kwargs["stop_loss_pct"])
                if kwargs["secure"]:
                    trailing_stop = entry_price * (1. + kwargs["trailing_stop_pct"])
            elif row["Low price"] < stop_loss:
                capital = positions * stop_loss
                positions = 0.

            current_capital = capital if positions == 0. else positions * row["Close price"]
            peak = max(current_capital, peak)
            current_drawdown = (peak - current_capital) / peak
            drawdown = max(current_drawdown, drawdown)
            capital_curve.append(current_capital)

        return InvestResult(capital_start=self._capital_start, capital_end=current_capital, drawdown=drawdown,
                            capital_curve=capital_curve, positions_end=positions)
