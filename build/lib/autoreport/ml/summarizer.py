from __future__ import annotations
from typing import List, Dict, Any
from ..core.models import SummaryItem, SummaryReport

def build_summary(analysis: Dict[str, Any]) -> SummaryReport:
    bullets: List[SummaryItem] = []
    best = analysis.get("best", {})
    base = analysis.get("baseline", {})
    metric = analysis.get("main_metric", "accuracy")
    if metric in best and metric in base:
        delta = best[metric] - base[metric]
        txt = f"Лучшая модель: {best.get('model','unknown')} с {metric}={best[metric]:.3f} ({delta:+.2%} к baseline)."
        bullets.append(SummaryItem(text=txt, score=1.0, evidence={"metric": metric, "delta": delta}))
    risk = analysis.get("risk_level", "low")
    if risk != "low":
        bullets.append(SummaryItem(text=f"Риск эксперимента: {risk}. Проверьте sanity-checks.", score=0.8))
    return SummaryReport(bullets=bullets)