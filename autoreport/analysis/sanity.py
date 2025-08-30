from __future__ import annotations
from typing import Dict, Any, List
import numpy as np

def class_imbalance(y_true: np.ndarray) -> Dict[str, Any]:
    vals, cnts = np.unique(y_true, return_counts=True)
    total = cnts.sum()
    if total:
        ratio = cnts.min() / total
    else:
        ratio = 0.0
    return {"name": "class_imbalance", "ratio_min": float(ratio), "level": "warn" if ratio < 0.1 else "ok"}

def missing_prob_for_auc(y_true: np.ndarray, has_prob: bool) -> Dict[str, Any]:
    uniq = np.unique(y_true)
    need_prob = (len(uniq) == 2)
    if need_prob and not has_prob:
        return {"name": "missing_prob", "level": "warn", "msg": "No y_prob for ROC/PR"}
    return {"name": "missing_prob", "level": "ok"}

def aggregate_risk(findings: List[Dict[str, Any]]) -> str:
    score = 0
    for f in findings:
        if f.get("level") == "warn":
            score += 1
        if f.get("level") == "high":
            score += 2
    if score >= 3:
        return "high"
    if score >= 1:
        return "medium"
    return "low"
