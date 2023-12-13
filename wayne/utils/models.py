# coding=utf-8

""" All binance models. """

from pydantic import BaseModel


class RateLimit(BaseModel, frozen=True):
    rateLimitType: str
    interval: str
    limit: int


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
    filters: list[dict]  # TODO: Provide strong typing
    permissions: list[str]
    defaultSelfTradePreventionMode: str
    allowedSelfTradePreventionModes: list[str]


class Product(BaseModel, frozen=True):
    timezone: str
    serverTime: int
    rateLimits: list[RateLimit]
    exchangeFilters: list
    symbols: list[Symbol]
