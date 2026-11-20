from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import LoadBatch
from ..schemas import BatchOut, ReconcileOut
from ..services.reconcile import build_reconcile

router = APIRouter(prefix="/api", tags=["reconcile"])


@router.get("/reconcile", response_model=ReconcileOut)
def reconcile(db: Session = Depends(get_db)):
    return build_reconcile(db)


@router.get("/batches", response_model=list[BatchOut])
def list_batches(db: Session = Depends(get_db)):
    return db.scalars(select(LoadBatch).order_by(LoadBatch.id.desc()).limit(100)).all()
