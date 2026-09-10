import enum
from decimal import Decimal

from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Numeric, DateTime, func, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column

class Base(DeclarativeBase):
    pass

class TimeStamp(Base):
    __abstract__ = True
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at : Mapped[datetime] = mapped_column(DateTime(timezone=True),server_default=func.now(), onupdate=func.now())

class OrderSide(str, enum.Enum):
    BUY="BUY"
    SELL="SELL"

class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"

class OrderStatus(str, enum.Enum):
    PENDING="PENDING"
    FILLED="FILLED"
    CANCELLED="CANCELLED"

class User(TimeStamp):
    __tablename__ = "users"
    id : Mapped[int] = mapped_column(primary_key=True)
    username : Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email : Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    password : Mapped[str] = mapped_column(String(255), nullable=False) #hashed

    available_funds : Mapped[int] = mapped_column(Numeric(14,2), default=Decimal(10000000), nullable=False)
    holdings : Mapped[List["Holding"]] = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    orders : Mapped[List["Order"]] = relationship("Order", back_populates="user", cascade="all, delete-orphan")

class Holding(TimeStamp):
    __tablename__  = "holdings"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    symbol : Mapped[str] = mapped_column(String(15), index=True, nullable=False)

    quantity : Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    average_price : Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)

    user : Mapped[User] = relationship("User", back_populates="holdings")

    __table_args__ = (
        UniqueConstraint("user_id", "symbol",  name="unique_user_symbol_holding"),
    )

class Order(TimeStamp):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    symbol : Mapped[str] = mapped_column(String(15), index=True, nullable=False)
    order_type : Mapped[str] = mapped_column(Enum(OrderType), nullable=False)
    order_side : Mapped[str] = mapped_column(Enum(OrderSide), nullable=False)
    status : Mapped[str] = mapped_column(Enum(OrderStatus), nullable=False)

    quantity : Mapped[Decimal] = mapped_column(Numeric(precision=10, scale=2), nullable=False)
    execution_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    limit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=14, scale=2), nullable=True)
    total_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(precision=14, scale=2), nullable=True)

    completed_at : Mapped[datetime] = mapped_column(DateTime(timezone=True))
    user : Mapped[User] = relationship("User", back_populates="orders")
    stock_exchange : Mapped[str] = mapped_column(String(6))
    __table_args__ = (
        Index("index_order_user_status", "user_id", "status"),
    )