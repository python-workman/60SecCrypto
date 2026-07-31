import asyncio
from typing import Optional

from celery.utils.log import get_task_logger

import aiohttp
from pydantic import BaseModel, ValidationError

logger = get_task_logger(__name__)


class DeribitAPIError(Exception):
    """Базовое исключение для ошибок, возвращаемых API Deribit."""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Deribit API error {code}: {message}")


class DeribitIndexResult(BaseModel):
    index_price: float
    estimated_delivery_price: float


class DeribitResponse(BaseModel):
    result: Optional[DeribitIndexResult] = None
    error: Optional[dict] = None


class DeribitClient:
    """Асинхронный клиент для публичных методов Deribit (JSON-RPC 2.0)."""

    def __init__(self, base_url: str = "https://deribit.com/api/v2"):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/api/v2"):
            self.base_url += "/api/v2"
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()

    async def get_index_price(self, ticker: str, retries: int = 3):
        """
        Возвращает текущую index_price для указанного тикера.
        """
        if not self._session:
            raise RuntimeError(
                "Сессия не инициализирована. Используйте контекстный менеджер."
            )

        url = f"{self.base_url}/public/get_index_price"
        params = {"index_name": ticker}

        for attempt in range(1, retries + 1):
            try:
                async with self._session.get(url, params=params) as response:
                    if response.status != 200:
                        text = await response.text()
                        raise aiohttp.ClientError(
                            f"HTTP {response.status}: {text[:200]}"
                        )

                    raw_data = await response.json()
                    if "error" in raw_data and raw_data["error"]:
                        err = raw_data["error"]
                        raise DeribitAPIError(
                            code=err.get("code", -1),
                            message=err.get("message", "Unknown error")
                        )

                    try:
                        validated = DeribitResponse.model_validate(raw_data)
                        if validated.result is None:
                            raise ValueError("Пустой result в ответе")
                        return validated.result.index_price
                    except ValidationError as e:
                        raise ValueError(f"Некорректная структура ответа: {e}")

            except DeribitAPIError:
                raise
            except (
                aiohttp.ClientError,
                ValueError,
                asyncio.TimeoutError
            ) as e:
                logger.warning(
                    f"Попытка {attempt}/{retries} "
                    f"для {ticker} не удалась: {e}"
                )
                if attempt == retries:
                    raise
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError(
            f"Не удалось получить цену для {ticker} "
            f"после {retries} попыток."
        )
