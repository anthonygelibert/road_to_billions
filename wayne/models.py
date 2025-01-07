"""All models used by Wayne."""

from __future__ import annotations

from typing import Annotated, TypedDict

from pydantic import BaseModel, ConfigDict, Field, NonNegativeFloat, PositiveFloat

type Between0And1 = Annotated[float, Field(ge=0., le=1.)]  # noqa:E252 # False positive from ruff.


class TrailingStopParameters(TypedDict):
    """Parameters for a trailing stop strategy."""

    stop_loss_pct: Between0And1
    trailing_stop_pct: Between0And1


class EMARSIBuyOrderGeneratorParameters(TypedDict):
    """Parameters for a EMA RSI buy order generator strategy."""

    ema_window: int
    rsi_window: int
    rsi_threshold: float


class InvestResult(BaseModel):
    """Result of an investment strategy."""

    model_config = ConfigDict(frozen=True)

    capital_start: PositiveFloat
    """Capital start."""
    capital_end: float
    """Capital end."""
    positions_end: NonNegativeFloat
    """Positions at end."""
    drawdown: Between0And1
    """Drawdown."""
    platform_fees: float
    """Platform fees."""
    capital_curve: list[float]
    """Capital curve."""

    @property
    def profit(self) -> float:
        """Profit on the period."""
        return self.capital_end - self.capital_start

    @property
    def profit_percentage(self) -> float:
        """Profit (percentage) on the period."""
        return (self.profit / self.capital_start) * 100.

    @property
    def max(self) -> float:
        """Maximum value of the capital on the period."""
        return max(self.capital_curve)

    @property
    def min(self) -> float:
        """Minimal value of the capital on the period."""
        return min(self.capital_curve)

    @property
    def capital_structure(self) -> str:
        """Structure of the capital at the end of the period."""
        return "liquidity" if self.positions_end == 0. else (f"{self.positions_end:.2f} x "
                                                             f"{self.capital_end / self.positions_end:.2f}")
