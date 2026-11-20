from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import BindRun, BoundFact, DimensionRow, UnboundFact


def _latest_active_dims(db: Session) -> dict[str, DimensionRow]:
    rows = db.scalars(select(DimensionRow).where(DimensionRow.status == "active")).all()
    latest: dict[str, DimensionRow] = {}
    for row in rows:
        cur = latest.get(row.bind_key)
        if cur is None or row.version > cur.version:
            latest[row.bind_key] = row
    return latest


def run_bind(
    db: Session,
    *,
    run_key: str | None = None,
    note: str = "",
    bind_keys: list[str] | None = None,
) -> BindRun:
    key = run_key or f"bind-{uuid4().hex[:12]}"
    dims = _latest_active_dims(db)

    q = select(UnboundFact)
    if bind_keys:
        q = q.where(UnboundFact.bind_key.in_(bind_keys))
    unbound = db.scalars(q).all()

    bound_count = 0
    skipped = 0
    for fact in unbound:
        dim = dims.get(fact.bind_key)
        if dim is None:
            skipped += 1
            continue
        exists = db.scalar(select(BoundFact).where(BoundFact.fact_id == fact.fact_id))
        if exists:
            db.delete(fact)
            skipped += 1
            continue
        db.add(
            BoundFact(
                fact_id=fact.fact_id,
                bind_key=fact.bind_key,
                dim_version=dim.version,
                dim_label=dim.label,
                amount=fact.amount,
                event_at=fact.event_at,
                fact_batch_key=fact.batch_key,
                bind_batch_key=key,
            )
        )
        db.delete(fact)
        bound_count += 1

    run = BindRun(run_key=key, bound_count=bound_count, skipped_count=skipped, note=note)
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


def quarantine_older_than(db: Session, older_than: datetime, reason: str = "over_age") -> int:
    from ..models import QuarantineFact

    if older_than.tzinfo is None:
        older_than = older_than.replace(tzinfo=timezone.utc)

    rows = db.scalars(select(UnboundFact).where(UnboundFact.event_at < older_than)).all()
    moved = 0
    for fact in rows:
        exists = db.scalar(select(QuarantineFact).where(QuarantineFact.fact_id == fact.fact_id))
        if exists:
            db.delete(fact)
            continue
        db.add(
            QuarantineFact(
                fact_id=fact.fact_id,
                bind_key=fact.bind_key,
                amount=fact.amount,
                event_at=fact.event_at,
                reason=reason,
                source_batch_key=fact.batch_key,
            )
        )
        db.delete(fact)
        moved += 1
    db.commit()
    return moved
