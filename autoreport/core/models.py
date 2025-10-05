from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

class Metric(BaseModel):
    name: str
    value: float
    direction: str = Field("max", description="max|min, для сортировки best-run")
    std: Optional[float] = None

class MetricSeries(BaseModel):
    name: str
    points: List[Tuple[int, float]] = Field(default_factory=list) # (step, value)

class Artifact(BaseModel):
    name: str
    path: str  # changed to str to simplify JSON and template usage
    kind: str = "figure" # figure|file|model|other
    mime: Optional[str] = None
    sha256: Optional[str] = None
    size_bytes: Optional[int] = None

class Run(BaseModel):
    id: str
    name: str
    started_at: Optional[datetime] = None
    duration_s: float = 0.0
    params: Dict[str, Any] = Field(default_factory=dict)
    metrics: Dict[str, Metric] = Field(default_factory=dict)
    series: Dict[str, MetricSeries] = Field(default_factory=dict)
    artifacts: List[Artifact] = Field(default_factory=list)
    code: str = ""
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

class ExperimentSet(BaseModel):
    runs: List[Run] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)

class AnalysisResult(BaseModel):
    task_type: str # "classification"|"regression"|"unknown"
    summary_metrics: List[str] = Field(default_factory=list)
    best_run_id: Optional[str] = None
    comparison_table: List[Dict[str, Any]] = Field(default_factory=list)
    sanity_findings: List[Dict[str, Any]] = Field(default_factory=list)
    risk_level: str = "low"
    charts: Dict[str, str] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)

class SummaryItem(BaseModel):
    text: str
    score: float
    evidence: Dict[str, Any] = Field(default_factory=dict)

class SummaryReport(BaseModel):
    bullets: List[SummaryItem] = Field(default_factory=list)