from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import BoundFact, LoadBatch, QuarantineFact, UnboundFact
from ..schemas import FactBatchIn, UnboundOut

router = APIRouter(prefix="/api/facts", tags=["facts"])


@router.post("/ingest")
def ingest_facts(body: FactBatchIn, db: Session = Depends(get_db)):
    exists = db.scalar(select(LoadBatch).where(LoadBatch.batch_key == body.batch_key))
    if exists:
        raise HTTPException(409, f"批次已存在: {body.batch_key}")

    inserted = 0
    for row in body.facts:
        if db.scalar(select(UnboundFact).where(UnboundFact.fact_id == row.fact_id)):
            raise HTTPException(409, f"未绑区已有 fact_id: {row.fact_id}")
        if db.scalar(select(BoundFact).where(BoundFact.fact_id == row.fact_id)):
            raise HTTPException(409, f"正式区已有 fact_id: {row.fact_id}")
        if db.scalar(select(QuarantineFact).where(QuarantineFact.fact_id == row.fact_id)):
            raise HTTPException(409, f"隔离区已有 fact_id: {row.fact_id}")
        db.add(
            UnboundFact(
                fact_id=row.fact_id,
                bind_key=row.bind_key,
                amount=row.amount,
                event_at=row.event_at,
                batch_key=body.batch_key,
                payload=row.payload,
            )
        )
        inserted += 1

    db.add(
        LoadBatch(
            batch_key=body.batch_key,
            kind="fact",
            row_count=inserted,
            note=body.note,
        )
    )
    db.commit()
    return {"batch_key": body.batch_key, "inserted": inserted}


@router.get("/unbound", response_model=list[UnboundOut])
def list_unbound(db: Session = Depends(get_db)):
    rows = db.scalars(select(UnboundFact).order_by(UnboundFact.id.desc()).limit(200)).all()
    return rows
