from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CodeAnalyzeRequest(BaseModel):
    code: str = Field(min_length=1)
    filename: str = "pasted_code.py"
    language: str = "python"


class Issue(BaseModel):
    line: int
    column: int = 0
    rule: str
    severity: Literal["info", "minor", "major", "critical"]
    message: str
    suggestion: str


class ScoreCard(BaseModel):
    cyclomatic_complexity: float
    maintainability_score: float
    readability_score: float
    quality_score: float


class AnalysisResult(BaseModel):
    filename: str
    language: str
    issues: list[Issue]
    duplicate_blocks: list[dict[str, Any]]
    ai_suggestions: list[str]
    scores: ScoreCard
    metrics: dict[str, Any]


class ScanSummary(BaseModel):
    id: int
    filename: str
    total_issues: int
    complexity: float
    maintainability_score: float
    readability_score: float
    quality_score: float
    created_at: datetime

    model_config = {"from_attributes": True}
