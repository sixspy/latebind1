from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import DimensionRow, LoadBatch
from ..schemas import DimBatchIn, DimOut

router = APIRouter(prefix="/api/dimensions", tags=["dimensions"])


@router.post("/ingest")
def ingest_dims(body: DimBatchIn, db: Session = Depends(get_db)):
    exists = db.scalar(select(LoadBatch).where(LoadBatch.batch_key == body.batch_key))
    if exists:
        raise HTTPException(409, f"批次已存在: {body.batch_key}")

    inserted = 0
    for row in body.rows:
        conflict = db.scalar(
            select(DimensionRow).where(
                DimensionRow.bind_key == row.bind_key,
                DimensionRow.version == row.version,
            )
        )
        if conflict:
            raise HTTPException(409, f"维度版本已存在: {row.bind_key}@v{row.version}")
        db.add(
            DimensionRow(
                bind_key=row.bind_key,
                version=row.version,
                label=row.label,
                status=row.status,
                batch_key=body.batch_key,
            )
        )
        inserted += 1

    db.add(
        LoadBatch(
            batch_key=body.batch_key,
            kind="dimension",
            row_count=inserted,
            note=body.note,
        )
    )
    db.commit()
    return {"batch_key": body.batch_key, "inserted": inserted}


@router.get("/", response_model=list[DimOut])
def list_dims(db: Session = Depends(get_db)):
    rows = db.scalars(select(DimensionRow).order_by(DimensionRow.id.desc()).limit(200)).all()
    return rows
