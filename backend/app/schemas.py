from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class FactIn(BaseModel):
    fact_id: str
    bind_key: str
    amount: float = 0.0
    event_at: datetime
    payload: str = "{}"


class FactBatchIn(BaseModel):
    batch_key: str
    note: str = ""
    facts: list[FactIn] = Field(min_length=1)


class DimIn(BaseModel):
    bind_key: str
    version: int = 1
    label: str = ""
    status: str = "active"


class DimBatchIn(BaseModel):
    batch_key: str
    note: str = ""
    rows: list[DimIn] = Field(min_length=1)


class BindRequest(BaseModel):
    run_key: Optional[str] = None
    note: str = ""
    # 仅绑定这些 key；空则尝试全部未绑
    bind_keys: list[str] = Field(default_factory=list)


class QuarantineRequest(BaseModel):
    # 事件时间早于该时刻且仍未绑 → 隔离（ISO8601）
    older_than: datetime
    reason: str = "over_age"


class BatchOut(BaseModel):
    id: int
    batch_key: str
    kind: str
    row_count: int
    note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UnboundOut(BaseModel):
    fact_id: str
    bind_key: str
    amount: float
    event_at: datetime
    batch_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DimOut(BaseModel):
    bind_key: str
    version: int
    label: str
    status: str
    batch_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BoundOut(BaseModel):
    fact_id: str
    bind_key: str
    dim_version: int
    dim_label: str
    amount: float
    event_at: datetime
    fact_batch_key: str
    bind_batch_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class QuarantineOut(BaseModel):
    fact_id: str
    bind_key: str
    amount: float
    event_at: datetime
    reason: str
    source_batch_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class BindResult(BaseModel):
    run_key: str
    bound_count: int
    skipped_count: int
    note: str


class QuarantineResult(BaseModel):
    moved: int
    reason: str


class ReconcileOut(BaseModel):
    unbound_count: int
    bound_count: int
    quarantine_count: int
    dim_active_keys: int
    unbound_keys_missing_dim: int
    bound_keys_missing_dim: int
    amount_unbound: float
    amount_bound: float
    amount_quarantine: float
    ok: bool
    messages: list[str]
