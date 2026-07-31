from pydantic import BaseModel


class PriceResponseSchema(BaseModel):
    ticker: str
    price: float
    timestamp: int

    class Config:
        from_attributes = True
