"""Binance HL API."""

from __future__ import annotations

import json
from typing import Final, TYPE_CHECKING

import pandas as pd
from binance.spot import Spot

from models import CoinInfo

if TYPE_CHECKING:
    from pathlib import Path


class Client:
    """Custom Binance client."""

    COLUMNS: Final[list[str]] = ["Open time", "Open price", "High price", "Low price", "Close price", "Volume",
                                 "Kline close time", "Quote asset volume", "Number of trades",
                                 "Taker buy base asset volume", "Taker buy quote asset volume", "Ignore"]

    COLUMNS_TYPE: Final[dict[str, str]] = {"Open time": "datetime64[ms]", "Kline close time": "datetime64[ms]",
                                           "Open price": "float", "High price": "float", "Low price": "float",
                                           "Close price": "float", "Volume": "float", "Quote asset volume": "float",
                                           "Number of trades": "int", "Taker buy base asset volume": "float",
                                           "Taker buy quote asset volume": "float", "Ignore": "int"}

    def __init__(self, api_key: str | None = None, api_secret: str | None = None) -> None:
        self.client = Spot(api_key, api_secret)

    def coin_info(self, *, from_fake: Path | None = None) -> list[CoinInfo]:
        """Coin information."""
        # noinspection PyArgumentList
        rcis = json.loads(from_fake.read_text(encoding="utf-8")) if from_fake else self.client.coin_info()
        return [CoinInfo.model_validate(rci) for rci in rcis if
                not rci["isLegalMoney"] and rci["trading"] and rci["coin"] != "USDT"]

    def save_coin_info(self, path: Path) -> None:
        """Save coin information."""
        # noinspection PyArgumentList
        path.write_text(json.dumps(self.client.coin_info()), encoding="utf-8")

    def get_day_data(self, symbol: str, *, limit: int | None = None) -> pd.DataFrame:
        """Get data at day granularity."""
        # noinspection PyArgumentList
        return self._type_df(self._raw_day_data(symbol, limit=limit))

    def get_day_hour_data(self, symbol: str, *, limit: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Get data at day and hour granularity."""
        kls_day = self._raw_day_data(symbol=symbol, limit=limit)

        oldest_time = kls_day.iloc[0]["Open time"]
        kls_hour = self._raw_hour_data(symbol=symbol, start_time=oldest_time)
        while kls_day.iloc[-1]["Open time"] > kls_hour.iloc[-1]["Open time"]:
            next_start_time = kls_hour.iloc[-1]["Open time"] + 3600000
            next_data = self._raw_hour_data(symbol=symbol, start_time=next_start_time)
            kls_hour = pd.concat([kls_hour, next_data])

        return self._type_df(kls_day), self._type_df(kls_hour)

    def _raw_day_data(self, symbol: str, *, limit: int | None = None, start_time: int | None = None) -> pd.DataFrame:
        # noinspection PyArgumentList
        return pd.DataFrame(self.client.ui_klines(symbol=symbol, interval="1d", limit=limit, startTime=start_time),
                            columns=self.COLUMNS)

    def _raw_hour_data(self, symbol: str, *, start_time: int) -> pd.DataFrame:
        # noinspection PyArgumentList
        return pd.DataFrame(self.client.ui_klines(symbol=symbol, interval="1h", limit=1000, startTime=start_time),
                            columns=self.COLUMNS)

    @staticmethod
    def _type_df(data: pd.DataFrame) -> pd.DataFrame:
        """Convert dataframe."""
        return data.astype(Client.COLUMNS_TYPE).set_index("Open time")
