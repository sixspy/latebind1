from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import BoundFact, DimensionRow, QuarantineFact, UnboundFact
from ..schemas import ReconcileOut


def build_reconcile(db: Session) -> ReconcileOut:
    unbound_count = db.scalar(select(func.count()).select_from(UnboundFact)) or 0
    bound_count = db.scalar(select(func.count()).select_from(BoundFact)) or 0
    quarantine_count = db.scalar(select(func.count()).select_from(QuarantineFact)) or 0

    amount_unbound = db.scalar(select(func.coalesce(func.sum(UnboundFact.amount), 0.0))) or 0.0
    amount_bound = db.scalar(select(func.coalesce(func.sum(BoundFact.amount), 0.0))) or 0.0
    amount_quarantine = db.scalar(select(func.coalesce(func.sum(QuarantineFact.amount), 0.0))) or 0.0

    active_dims = db.scalars(select(DimensionRow).where(DimensionRow.status == "active")).all()
    latest_keys: set[str] = set()
    for d in active_dims:
        latest_keys.add(d.bind_key)
    dim_active_keys = len(latest_keys)

    unbound_keys = {r.bind_key for r in db.scalars(select(UnboundFact)).all()}
    bound_keys = {r.bind_key for r in db.scalars(select(BoundFact)).all()}

    missing_unbound = len(unbound_keys - latest_keys)
    missing_bound = len(bound_keys - latest_keys)

    messages: list[str] = []
    ok = True
    if missing_unbound:
        ok = False
        messages.append(f"未绑区有 {missing_unbound} 个绑定键缺少活跃维度（等待晚到维）。")
    if missing_bound:
        ok = False
        messages.append(f"正式区有 {missing_bound} 个绑定键当前无活跃维度（历史绑定仍保留）。")
    if not messages:
        messages.append("互证通过：未绑缺维仅为等待态时请人工确认批次水位。")

    return ReconcileOut(
        unbound_count=unbound_count,
        bound_count=bound_count,
        quarantine_count=quarantine_count,
        dim_active_keys=dim_active_keys,
        unbound_keys_missing_dim=missing_unbound,
        bound_keys_missing_dim=missing_bound,
        amount_unbound=float(amount_unbound),
        amount_bound=float(amount_bound),
        amount_quarantine=float(amount_quarantine),
        ok=ok,
        messages=messages,
    )
