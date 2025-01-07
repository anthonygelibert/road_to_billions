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


class Network(BaseModel):
    """Network information."""

    model_config = ConfigDict(frozen=True)

    network: str
    coin: str
    withdraw_integer_multiple: Annotated[float, Field(alias="withdrawIntegerMultiple")]
    is_default: Annotated[bool, Field(alias="isDefault")]
    deposit_enable: Annotated[bool, Field(alias="depositEnable")]
    withdraw_enable: Annotated[bool, Field(alias="withdrawEnable")]
    deposit_desc: Annotated[str, Field(alias="depositDesc")]
    withdraw_desc: Annotated[str, Field(alias="withdrawDesc")]
    special_tips: Annotated[str, Field(alias="specialTips")]
    special_withdraw_tips: Annotated[str, Field(alias="specialWithdrawTips")]
    name: str
    reset_address_status: Annotated[bool, Field(alias="resetAddressStatus")]
    address_regex: Annotated[str, Field(alias="addressRegex")]
    memo_regex: Annotated[str, Field(alias="memoRegex")]
    withdraw_fee: Annotated[float, Field(alias="withdrawFee")]
    withdraw_min: Annotated[float, Field(alias="withdrawMin")]
    withdraw_max: Annotated[float, Field(alias="withdrawMax")]
    withdraw_internal_min: Annotated[float, Field(alias="withdrawInternalMin")]
    deposit_dust: Annotated[float | None, Field(alias="depositDust")] = None
    min_confirm: Annotated[int, Field(alias="minConfirm")]
    un_lock_confirm: Annotated[int, Field(alias="unLockConfirm")]
    same_address: Annotated[bool, Field(alias="sameAddress")]
    estimated_arrival_time: Annotated[int, Field(alias="estimatedArrivalTime")]
    busy: bool
    contract_address_url: Annotated[str | None, Field(alias="contractAddressUrl")] = None
    contract_address: Annotated[str | None, Field(alias="contractAddress")] = None


class CoinInfo(BaseModel):
    """Coin information."""

    model_config = ConfigDict(frozen=True)

    coin: str
    deposit_all_enable: Annotated[bool, Field(alias="depositAllEnable")]
    withdraw_all_enable: Annotated[bool, Field(alias="withdrawAllEnable")]
    name: str
    free: float
    locked: float
    freeze: float
    withdrawing: float
    ipoing: float
    ipoable: float
    storage: float
    is_legal_money: Annotated[bool, Field(alias="isLegalMoney")]
    trading: bool
    network_list: Annotated[list[Network], Field(alias="networkList")]

    @property
    def symbol(self) -> str:
        """Symbol of the coin."""
        return f"{self.coin}USDT"
