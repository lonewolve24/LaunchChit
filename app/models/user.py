from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    otp_codes: Mapped[list["OTPCode"]] = relationship(back_populates="user")  # noqa: F821
    products: Mapped[list["Product"]] = relationship(back_populates="maker", foreign_keys="Product.maker_id")  # noqa: F821
    votes: Mapped[list["Vote"]] = relationship(back_populates="user", foreign_keys="Vote.user_id")  # noqa: F821
