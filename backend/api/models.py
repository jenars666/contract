from typing import Optional

from pydantic import BaseModel, Field


class VulnerabilityItem(BaseModel):
    id: str
    type: str
    title: str
    severity: str
    lines: list[int] = Field(default_factory=list)
    description: str
    source: Optional[str] = "Static Analysis"


class AnalyzeRequest(BaseModel):
    code: str
    filename: Optional[str] = "contract.sol"


class ValidationResult(BaseModel):
    status: str
    passed: bool
    original_count: int
    patched_count: int
    risk_score_before: int
    risk_score_after: int


class AnalyzeResponse(BaseModel):
    success: bool
    vulnerabilities: list[VulnerabilityItem]
    risk_score: int
    analysis_time: float
    filename: str
    error: Optional[str] = None


class PatchRequest(BaseModel):
    code: str
    vulnerabilities: list[VulnerabilityItem]


class PatchResponse(BaseModel):
    success: bool
    patched_code: str
    explanation: str
    changes_summary: list[str]
    validation: ValidationResult
    patch_time: float
    github_pushed: bool = False
    github_url: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    slither_available: bool


class PushRequest(BaseModel):
    filename: str
    code: str
    commit_message: Optional[str] = None


class PushResponse(BaseModel):
    success: bool
    url: Optional[str] = None
    commit: Optional[str] = None
    error: Optional[str] = None
