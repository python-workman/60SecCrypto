from sqlalchemy import BigInteger, Float, Index, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TickerPrice(Base):
    __tablename__ = "ticker_prices"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    ticker: Mapped[str] = mapped_column(String(10), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        Index("ix_ticker_timestamp", "ticker", "timestamp"),
    )
