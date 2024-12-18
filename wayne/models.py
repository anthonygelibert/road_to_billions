"""All models used by Wayne."""

from __future__ import annotations

from typing import Annotated, TypedDict

from pydantic import BaseModel, confloat, NonNegativeFloat, PositiveFloat


class TrailingStopParameters(TypedDict):
    """Parameters for a trailing stop strategy."""

    secure: bool
    stop_loss_pct: float
    trailing_stop_pct: float


class InvestResult(BaseModel):
    """Result of an investment strategy."""

    capital_start: PositiveFloat
    """Capital start."""
    capital_end: float
    """Capital end."""
    positions_end: NonNegativeFloat
    """Positions at end."""
    drawdown: Annotated[float, confloat(ge=0., le=1.)]
    """Drawdown."""
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
