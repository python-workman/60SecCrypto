from typing import Optional

import aiohttp
from pydantic import BaseModel


class DeribitIndexResult(BaseModel):
    index_price: float
    estimated_delivery_price: float


class DeribitResponse(BaseModel):
    result: DeribitIndexResult


class DeribitClient:
    def __init__(self, base_url: str = "https://test.deribit.com/api/v2"):
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def get_index_price(self, ticker: str) -> float:
        """
        Принимает тикер (btc_usd или eth_usd),
        делает запрос к Deribit и возвращает чистый float цены.
        """
        if not self._session:
            raise RuntimeError(
                "Сессия не инициализирована."
            )

        url = self.base_url.rstrip("/")
        if not url.endswith("/api/v2"):
            url = f"{url}/api/v2"

        final_url = f"{url}/public/get_index_price"
        params = {"index_name": ticker}

        try:
            async with self._session.get(final_url, params=params) as response:
                if response.status != 200:
                    text = await response.text()
                    raise Exception(
                        f"Deribit API вернул статус {response.status}: "
                        f"{text[:100]}"
                    )

                raw_data = await response.json()

                validated_data = DeribitResponse.model_validate(raw_data)
                return validated_data.result.index_price

        except aiohttp.ClientError as e:
            raise Exception(f"Ошибка сети при запросе к Deribit: {e}")
