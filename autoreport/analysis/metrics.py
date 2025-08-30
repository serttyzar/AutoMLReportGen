from __future__ import annotations
import numpy as np
from typing import Dict
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.metrics import f1_score, roc_auc_score, mean_squared_error, mean_absolute_error, r2_score
from math import sqrt


def infer_task_type(y_true: np.ndarray) -> str:
    uniq = np.unique(y_true)
    if np.issubdtype(y_true.dtype, np.floating) and len(uniq) > 10:
        return "regression"
    if len(uniq) <= 20:
        return "classification"
    return "classification"

def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray | None) -> Dict[str, float]:
    out = {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_w": float(precision_score(y_true, y_pred, average="weighted", zero_division=0)),
        "recall_w": float(recall_score(y_true, y_pred, average="weighted", zero_division=0)),
        "f1_w": float(f1_score(y_true, y_pred, average="weighted", zero_division=0)),
    }
    try:
        if y_prob is not None and getattr(y_prob, "ndim", 1) == 1:
            out["roc_auc"] = float(roc_auc_score(y_true, y_prob))
        else:
            uniq = np.unique(y_true)
            if len(uniq) == 2:
                out["roc_auc"] = float(roc_auc_score(y_true, y_pred))
    except Exception:
        pass
    return out

def regression_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mse = float(mean_squared_error(y_true, y_pred))
    return {
        "mse": mse,
        "rmse": sqrt(mse),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }