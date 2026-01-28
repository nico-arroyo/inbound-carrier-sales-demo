from sqlalchemy import String, Float, Integer, Boolean, BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class CallRecord(Base):
    __tablename__ = "calls"

    call_id: Mapped[str] = mapped_column(String, primary_key=True)

    ended_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    outcome: Mapped[str | None] = mapped_column(String, nullable=True)
    sentiment: Mapped[str | None] = mapped_column(String, nullable=True)
    verified: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    load_id: Mapped[str | None] = mapped_column(String, nullable=True)
    loadboard_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    rounds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    carrier_first_offer: Mapped[float | None] = mapped_column(Float, nullable=True)
    carrier_last_offer: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_offer: Mapped[float | None] = mapped_column(Float, nullable=True)

    agreed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    transfer_to_rep: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
