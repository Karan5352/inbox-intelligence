"""Automation workflow CRUD + run endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories import automation_repo
from app.schemas.action import AutomationIn, AutomationOut, AutomationRunResult
from app.services import automation_service

router = APIRouter(prefix="/automations", tags=["automations"])


@router.get("", response_model=list[AutomationOut])
def list_automations(db: Session = Depends(get_db)) -> list[AutomationOut]:
    return [
        AutomationOut.model_validate(a, from_attributes=True) for a in automation_repo.list_all(db)
    ]


@router.post("", response_model=AutomationOut, status_code=201)
def create_automation(payload: AutomationIn, db: Session = Depends(get_db)) -> AutomationOut:
    automation = automation_service.create(db, payload)
    return AutomationOut.model_validate(automation, from_attributes=True)


@router.delete("/{automation_id}", status_code=204)
def delete_automation(automation_id: int, db: Session = Depends(get_db)) -> None:
    if not automation_service.delete(db, automation_id):
        raise HTTPException(status_code=404, detail="Automation not found")


@router.post("/run", response_model=AutomationRunResult)
def run_automations(
    db: Session = Depends(get_db),
    dry_run: bool = Query(default=True, description="Preview matches without mutating."),
) -> AutomationRunResult:
    return automation_service.run_all(db, dry_run=dry_run)
