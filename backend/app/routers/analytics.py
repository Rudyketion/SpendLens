"""Analytics endpoints used by the dashboard."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services import analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/totals", response_model=schemas.TotalsOut)
def get_totals(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return analytics.totals(db, start, end)


@router.get("/categories", response_model=list[schemas.CategoryBreakdownItem])
def get_category_breakdown(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return analytics.category_breakdown(db, start, end)


@router.get("/timeseries", response_model=list[schemas.TimeseriesPoint])
def get_timeseries(
    bucket: str = Query(default="day", pattern="^(day|month)$"),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return analytics.timeseries(db, bucket=bucket, start=start, end=end)


@router.get("/insights", response_model=list[schemas.InsightOut])
def get_insights(
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return analytics.insights(db, start, end)
