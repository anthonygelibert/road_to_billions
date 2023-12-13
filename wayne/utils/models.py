# coding=utf-8

""" All binance models. """

from abc import ABC
from typing import Annotated

from pydantic import BaseModel, BeforeValidator


class RateLimit(BaseModel, frozen=True):
    rateLimitType: str
    interval: str
    limit: int


class Filter(ABC, BaseModel, frozen=True):
    filterType: str


class PriceFilter(Filter, frozen=True):
    filterType: str = 'PRICE_FILTER'
    minPrice: float
    maxPrice: float
    tickSize: float


class LotSizeFilter(Filter, frozen=True):
    filterType: str = 'LOT_SIZE'
    minQty: float
    maxQty: float
    stepSize: float


class IcebergPartsFilter(Filter, frozen=True):
    filterType: str = 'ICEBERG_PARTS'
    limit: float


class MarketLotSizeFilter(Filter, frozen=True):
    filterType: str = 'MARKET_LOT_SIZE'
    minQty: float
    maxQty: float
    stepSize: float


class TrailingDeltaFilter(Filter, frozen=True):
    filterType: str = 'TRAILING_DELTA'
    minTrailingAboveDelta: float
    maxTrailingAboveDelta: float
    minTrailingBelowDelta: float
    maxTrailingBelowDelta: float


class NotionalFilter(Filter, frozen=True):
    filterType: str = 'NOTIONAL'
    minNotional: float
    applyMinToMarket: bool
    maxNotional: float
    applyMaxToMarket: bool
    avgPriceMins: float


class PercentPriceBySideFilter(Filter, frozen=True):
    filterType: str = 'PERCENT_PRICE_BY_SIDE'
    bidMultiplierUp: float
    askMultiplierUp: float
    askMultiplierDown: float
    avgPriceMins: float


class MaxPositionFilter(Filter, frozen=True):
    filterType: str = 'MAX_POSITION'
    maxPosition: float


class MaxNumOrdersFilter(Filter, frozen=True):
    filterType: str = 'MAX_NUM_ORDERS'
    maxNumOrders: int


class MaxNumAlgoOrdersFilter(Filter, frozen=True):
    filterType: str = 'MAX_NUM_ALGO_ORDERS'
    maxNumAlgoOrders: int


ALL_FILTERS = {'PRICE_FILTER': PriceFilter, 'LOT_SIZE': LotSizeFilter, 'ICEBERG_PARTS': IcebergPartsFilter,
               'MARKET_LOT_SIZE': MarketLotSizeFilter, 'TRAILING_DELTA': TrailingDeltaFilter,
               'NOTIONAL': NotionalFilter, 'PERCENT_PRICE_BY_SIDE': PercentPriceBySideFilter,
               'MAX_POSITION': MaxPositionFilter, 'MAX_NUM_ORDERS': MaxNumOrdersFilter,
               'MAX_NUM_ALGO_ORDERS': MaxNumAlgoOrdersFilter}
""" Maps between a filter type and its model class. """


def select_filter(raw_filter: dict) -> Filter:
    """ Select the right model for a filter. """
    if (filter_type := raw_filter.get('filterType')) is None:
        raise ValueError(f"No type in this filter: {raw_filter}")
    if (cls := ALL_FILTERS.get(filter_type)) is None:
        raise ValueError(f"Unknown filter type: {filter_type}")
    return cls(**raw_filter)


class Symbol(BaseModel, frozen=True):
    symbol: str
    status: str
    baseAsset: str
    baseAssetPrecision: int
    quoteAsset: str
    quotePrecision: int
    quoteAssetPrecision: int
    baseCommissionPrecision: int
    quoteCommissionPrecision: int
    orderTypes: list[str]
    icebergAllowed: bool
    ocoAllowed: bool
    quoteOrderQtyMarketAllowed: bool
    allowTrailingStop: bool
    cancelReplaceAllowed: bool
    isSpotTradingAllowed: bool
    isMarginTradingAllowed: bool
    filters: list[Annotated[Filter, BeforeValidator(select_filter)]]
    permissions: list[str]
    defaultSelfTradePreventionMode: str
    allowedSelfTradePreventionModes: list[str]


class ExchangeInformation(BaseModel, frozen=True):
    timezone: str
    serverTime: int
    rateLimits: list[RateLimit]
    exchangeFilters: list
    symbols: list[Symbol]
