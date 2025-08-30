from __future__ import annotations
from typing import Dict, Any
import numpy as np
from ..core.models import ExperimentSet, Run
from ..analysis.sanity import class_imbalance, missing_prob_for_auc, aggregate_risk


def extract_main(y_true, y_pred, y_prob):
    return np.asarray(y_true), np.asarray(y_pred), (None if y_prob is None else np.asarray(y_prob))

def pick_metric(metrics: Dict[str, Any]) -> str:
    for k in ("roc_auc", "f1_w", "accuracy", "r2", "rmse", "mse"):
        if k in metrics:
            return k
    return next(iter(metrics.keys()), "accuracy")

def build_analysis(es: ExperimentSet) -> Dict[str, Any]:
    runs = es.runs
    if not runs:
        return {}
    baseline = runs[-2] if len(runs) >= 2 else runs[-1]
    best = runs[-1]
    main_metric = pick_metric(best.metrics)

    findings = []
    ns = {}
    
    if "roc_auc" not in best.metrics:
        findings.append({"name": "missing_prob", "level": "warn", "msg": "No y_prob for ROC/PR"})

    risk_level = aggregate_risk(findings) if findings else "low"

    return {
        "best": {k: v.value for k, v in best.metrics.items()},
        "baseline": {k: v.value for k, v in baseline.metrics.items()},
        "best_id": best.id,
        "baseline_id": baseline.id,
        "main_metric": main_metric,
        "sanity_findings": findings,
        "risk_level": risk_level,
    }
