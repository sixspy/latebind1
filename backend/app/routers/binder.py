from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import BindRun, BoundFact
from ..schemas import BindRequest, BindResult, BoundOut, QuarantineOut, QuarantineRequest, QuarantineResult
from ..models import QuarantineFact
from ..services.binder import quarantine_older_than, run_bind

router = APIRouter(prefix="/api/binder", tags=["binder"])


@router.post("/run", response_model=BindResult)
def bind_run(body: BindRequest, db: Session = Depends(get_db)):
    run = run_bind(db, run_key=body.run_key, note=body.note, bind_keys=body.bind_keys or None)
    return BindResult(
        run_key=run.run_key,
        bound_count=run.bound_count,
        skipped_count=run.skipped_count,
        note=run.note,
    )


@router.get("/bound", response_model=list[BoundOut])
def list_bound(db: Session = Depends(get_db)):
    return db.scalars(select(BoundFact).order_by(BoundFact.id.desc()).limit(200)).all()


@router.get("/runs")
def list_runs(db: Session = Depends(get_db)):
    rows = db.scalars(select(BindRun).order_by(BindRun.id.desc()).limit(50)).all()
    return [
        {
            "run_key": r.run_key,
            "bound_count": r.bound_count,
            "skipped_count": r.skipped_count,
            "note": r.note,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/quarantine", response_model=QuarantineResult)
def do_quarantine(body: QuarantineRequest, db: Session = Depends(get_db)):
    moved = quarantine_older_than(db, body.older_than, body.reason)
    return QuarantineResult(moved=moved, reason=body.reason)


@router.get("/quarantine", response_model=list[QuarantineOut])
def list_quarantine(db: Session = Depends(get_db)):
    return db.scalars(select(QuarantineFact).order_by(QuarantineFact.id.desc()).limit(200)).all()
