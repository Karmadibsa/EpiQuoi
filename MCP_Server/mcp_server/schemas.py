from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class CampusFormation(BaseModel):
    nom: str
    type: str


class CampusEntry(BaseModel):
    ville: str
    pays: str
    url: str
    formations_disponibles: List[CampusFormation] = Field(default_factory=list)


class ScrapeMeta(BaseModel):
    spider: str
    item_count: int
    duration_ms: int
    stderr_tail: Optional[str] = None


class ScrapeCampusResponse(BaseModel):
    data: List[Dict[str, Any]]
    meta: ScrapeMeta


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

