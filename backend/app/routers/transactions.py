"""Transaction list/create/update/delete."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("", response_model=list[schemas.TransactionOut])
def list_transactions(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    category_id: int | None = Query(default=None),
    q: str | None = Query(default=None, description="Substring search in description/merchant"),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    query = select(models.Transaction).options(joinedload(models.Transaction.category))
    if start:
        query = query.where(models.Transaction.occurred_on >= start)
    if end:
        query = query.where(models.Transaction.occurred_on <= end)
    if category_id:
        query = query.where(models.Transaction.category_id == category_id)
    if q:
        like = f"%{q.lower()}%"
        query = query.where(
            (models.Transaction.description.ilike(like))
            | (models.Transaction.merchant.ilike(like))
        )
    query = query.order_by(models.Transaction.occurred_on.desc(), models.Transaction.id.desc())
    query = query.limit(limit).offset(offset)
    return list(db.execute(query).scalars())


@router.post("", response_model=schemas.TransactionOut, status_code=201)
def create_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db)):
    tx = models.Transaction(**payload.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.patch("/{tx_id}", response_model=schemas.TransactionOut)
def update_transaction(tx_id: int, payload: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    tx = db.get(models.Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tx, field, value)
    db.commit()
    db.refresh(tx)
    return tx


@router.delete("/{tx_id}", status_code=204)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    tx = db.get(models.Transaction, tx_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(tx)
    db.commit()
