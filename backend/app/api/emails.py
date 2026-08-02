"""Email listing / detail endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import email_repo
from app.schemas.email import EmailDetail, EmailOut, EmailPage

router = APIRouter(prefix="/emails", tags=["emails"])


@router.get("", response_model=EmailPage)
def list_emails(
    db: Session = Depends(get_db),
    category: str | None = Query(default=None),
    unread: bool | None = Query(default=None),
    archived: bool | None = Query(default=False),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> EmailPage:
    rows, total = email_repo.list_emails(
        db,
        category=category,
        unread=unread,
        archived=archived,
        search=search,
        limit=limit,
        offset=offset,
    )
    return EmailPage(
        items=[EmailOut.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{email_id}", response_model=EmailDetail)
def get_email(email_id: int, db: Session = Depends(get_db)) -> EmailDetail:
    email = email_repo.get(db, email_id)
    if email is None:
        raise HTTPException(status_code=404, detail="Email not found")
    return EmailDetail.model_validate(email)
