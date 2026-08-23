"""Statement upload: parse, categorize, persist."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import categorizer, parser

router = APIRouter(prefix="/statements", tags=["statements"])


@router.get("", response_model=list[schemas.StatementOut])
def list_statements(db: Session = Depends(get_db)):
    return list(db.execute(select(models.Statement).order_by(models.Statement.uploaded_at.desc())).scalars())


@router.post("/upload", response_model=schemas.UploadResult)
async def upload_statement(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        file_type, parsed_rows = parser.parse_statement(file.filename, content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not parsed_rows:
        raise HTTPException(status_code=400, detail="No transactions found in file")

    statement = models.Statement(
        filename=file.filename,
        file_type=file_type,
        row_count=len(parsed_rows),
    )
    db.add(statement)
    db.flush()

    # Ensure all baseline categories exist
    _ensure_categories(db)
    cat_by_name = {c.name: c for c in db.execute(select(models.Category)).scalars()}

    items = [(r.description, float(r.amount)) for r in parsed_rows]
    predicted = categorizer.categorize_batch(items)

    imported = 0
    categorized = 0
    for row, cat_name in zip(parsed_rows, predicted, strict=True):
        category = cat_by_name.get(cat_name) or cat_by_name["Other"]
        tx = models.Transaction(
            occurred_on=row.occurred_on,
            description=row.description,
            amount=row.amount,
            currency=row.currency,
            merchant=row.merchant,
            raw_source=row.raw_source,
            category_id=category.id,
            statement_id=statement.id,
        )
        db.add(tx)
        imported += 1
        if cat_name != "Other":
            categorized += 1

    db.commit()
    db.refresh(statement)

    return schemas.UploadResult(
        statement=schemas.StatementOut.model_validate(statement),
        imported=imported,
        categorized=categorized,
    )


def _ensure_categories(db: Session) -> None:
    existing = {c.name for c in db.execute(select(models.Category)).scalars()}
    for cdef in categorizer.CATEGORIES:
        if cdef.name not in existing:
            db.add(models.Category(name=cdef.name, color=cdef.color, icon=cdef.icon))
    db.flush()


@router.delete("/{statement_id}", status_code=204)
def delete_statement(statement_id: int, db: Session = Depends(get_db)):
    statement = db.get(models.Statement, statement_id)
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    # Cascade delete transactions belonging to this statement.
    for tx in list(statement.transactions):
        db.delete(tx)
    db.delete(statement)
    db.commit()
