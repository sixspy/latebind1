from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LoadBatch(Base):
    __tablename__ = "load_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batch_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(32))  # fact | dimension
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UnboundFact(Base):
    __tablename__ = "unbound_facts"
    __table_args__ = (UniqueConstraint("fact_id", name="uq_unbound_fact_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fact_id: Mapped[str] = mapped_column(String(64), index=True)
    bind_key: Mapped[str] = mapped_column(String(128), index=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    batch_key: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DimensionRow(Base):
    __tablename__ = "dimensions"
    __table_args__ = (UniqueConstraint("bind_key", "version", name="uq_dim_key_ver"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bind_key: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    label: Mapped[str] = mapped_column(String(256), default="")
    status: Mapped[str] = mapped_column(String(32), default="active")  # active | retired
    batch_key: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BoundFact(Base):
    __tablename__ = "bound_facts"
    __table_args__ = (UniqueConstraint("fact_id", name="uq_bound_fact_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fact_id: Mapped[str] = mapped_column(String(64), index=True)
    bind_key: Mapped[str] = mapped_column(String(128), index=True)
    dim_version: Mapped[int] = mapped_column(Integer)
    dim_label: Mapped[str] = mapped_column(String(256), default="")
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fact_batch_key: Mapped[str] = mapped_column(String(64), index=True)
    bind_batch_key: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class QuarantineFact(Base):
    __tablename__ = "quarantine_facts"
    __table_args__ = (UniqueConstraint("fact_id", name="uq_quarantine_fact_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fact_id: Mapped[str] = mapped_column(String(64), index=True)
    bind_key: Mapped[str] = mapped_column(String(128), index=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    event_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reason: Mapped[str] = mapped_column(String(128), default="over_age")
    source_batch_key: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class BindRun(Base):
    __tablename__ = "bind_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    bound_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
