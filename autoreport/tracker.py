from __future__ import annotations
from typing import Dict, Any
import uuid
from pathlib import Path
from .core.models import Run, Metric
from .capture.figures import FigureManager
from .capture.variables import extract_predictions
from .analysis.metrics import infer_task_type, classification_metrics, regression_metrics
from .analysis.curves import plot_classification_curves, plot_regression_residuals


def run_experiment(code: str, namespace: Dict[str, Any], run_name: str, 
                   stdout: str, stderr: str, error: str | None, duration_s: float) -> Run:
    run_id = uuid.uuid4().hex[:10]
    preds = extract_predictions(namespace)
    metrics_map: Dict[str, float] = {}
    for label, vals in preds.items():
        y_t = vals.get("true"); y_p = vals.get("pred"); y_r = vals.get("prob")
        if y_t is None or y_p is None:
            continue
        task = infer_task_type(y_t)
        if task == "classification":
            metrics_map.update(classification_metrics(y_t, y_p, y_r))
            plot_classification_curves(y_t, y_p, y_r)
        else:
            metrics_map.update(regression_metrics(y_t, y_p))
            plot_regression_residuals(y_t, y_p)
        break
    figman = FigureManager()
    artifacts = figman.capture_current_figures()
    run = Run(
        id=run_id,
        name=run_name,
        duration_s=duration_s,
        params={}, # можно добавить log_params интерфейс
        metrics={k: Metric(name=k, value=v) for k, v in metrics_map.items()},
        series={},
        artifacts=artifacts,
        code=code,
        stdout=stdout,
        stderr=stderr,
        error=error,
        meta={},
    )
    return run