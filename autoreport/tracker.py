from __future__ import annotations
from typing import Dict, Any
import uuid
from pathlib import Path
from .core.models import Run, Metric, Artifact
from .capture.figures import FigureManager
from .capture.variables import extract_predictions, discover_labels
from .analysis.metrics import infer_task_type, classification_metrics, regression_metrics
from .analysis.curves import plot_classification_curves, plot_regression_residuals


def run_experiment(code: str, namespace: Dict[str, Any], run_name: str,
                   stdout: str, stderr: str, error: str | None, duration_s: float) -> Run:
    run_id = uuid.uuid4().hex[:10]
    preds = extract_predictions(namespace)

    metrics_map: Dict[str, Dict[str, float]] = {}

    # Перебираем все обнаруженные label'ы (несколько моделей/метрик)
    for label, vals in preds.items():
        y_t = vals.get("true"); y_p = vals.get("pred"); y_r = vals.get("prob")
        if y_t is None or y_p is None:
            continue
        task = infer_task_type(y_t)
        if task == "classification":
            mm = classification_metrics(y_t, y_p, y_r)
            # строим графики и сохраняем (plot_* возвращают dict метаданных)
            plot_classification_curves(y_t, y_p, y_r)
        else:
            mm = regression_metrics(y_t, y_p)
            plot_regression_residuals(y_t, y_p)
        metrics_map[label] = mm

    # захватываем все текущие фигуры
    figman = FigureManager()
    artifacts = figman.capture_current_figures()

    # сохраняем модели-метаданные (если есть)
    models_meta = {}
    for k, v in namespace.items():
        try:
            # простая эвристика: sklearn-подобные модели имеют attribute get_params
            if hasattr(v, 'get_params'):
                models_meta[k] = {
                    'type': v.__class__.__name__,
                    'params': getattr(v, 'get_params', lambda: {})()
                }
        except Exception:
            pass

    # сводим метрики в удобный формат для pydantic Run
    aggregated_metrics = {}
    for label, mm in metrics_map.items():
        for name, val in mm.items():
            key = f"{label}/{name}"
            aggregated_metrics[key] = Metric(name=key, value=float(val))

    run = Run(
        id=run_id,
        name=run_name,
        duration_s=duration_s,
        params={},
        metrics=aggregated_metrics,
        series={},
        artifacts=artifacts,
        code=code,
        stdout=stdout,
        stderr=stderr,
        error=error,
        meta={"models": models_meta}
    )
    return run


# Вспомогательная функция: если в namespace есть X и y, и есть объекты с predict — подставим y_pred_... автоматически

def inject_autopreds(namespace: Dict[str, Any]):
    # ищем источники X и y
    X = namespace.get('X') or namespace.get('X_train') or namespace.get('x')
    y = namespace.get('y') or namespace.get('y_train') or namespace.get('target')
    if X is None or y is None:
        return
    for name, obj in list(namespace.items()):
        if name.startswith('_'):
            continue
        if hasattr(obj, 'predict'):
            try:
                y_pred = obj.predict(X)
                namespace.setdefault(f'y_pred_{name}', y_pred)
                # try predict_proba
                if hasattr(obj, 'predict_proba'):
                    try:
                        y_prob = obj.predict_proba(X)
                        # if binary, keep 1d
                        if hasattr(y_prob, 'ndim') and y_prob.ndim == 2 and y_prob.shape[1] == 2:
                            namespace.setdefault(f'y_prob_{name}', y_prob[:, 1])
                        else:
                            namespace.setdefault(f'y_prob_{name}', y_prob)
                    except Exception:
                        pass
                # true
                namespace.setdefault(f'y_true_{name}', y)
            except Exception:
                # ignore prediction failures
                continue