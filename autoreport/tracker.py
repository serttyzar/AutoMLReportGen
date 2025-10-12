# autoreport/tracker.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
import uuid
from pathlib import Path
import inspect
from .capture.figures import FigureManager
from .capture.runtime import RuntimeCapture
from .capture.variables import discover_models_and_data
from .core.models import Run, Artifact, Metric
from .capture.lineage import collect_namespace_lineage


def _model_info(obj: Any) -> Dict[str, Any]:
    info: Dict[str, Any] = {"type": obj.__class__.__name__}
    try:
        if hasattr(obj, "get_params"):
            info["params"] = obj.get_params()
        else:
            info["params"] = getattr(obj, "__dict__", {}) or {}
    except Exception:
        info["params"] = {}
    return info


def run_experiment(code: str, namespace: Dict[str, Any], run_name: str,
                   stdout: str, stderr: str, error: str | None, duration_s: float,
                   artifacts: Optional[List[Artifact]] = None) -> Run:
    """
    Создаёт Run с привязкой моделей и метрик.
    Поддерживает scikit-learn и PyTorch (через collect_namespace_lineage).
    """
    run_id = uuid.uuid4().hex[:10]

    # --- 1️⃣ Получаем mapping моделей к данным ---
    mapping = discover_models_and_data(namespace)
    lineage_map = collect_namespace_lineage(namespace)
    for name, src in lineage_map.items():
        if "model" in src and hasattr(src["model"], "__class__"):
            mapping.setdefault(name, {"model": src["model"].__class__.__name__, "data": None})

    # --- 2️⃣ Метаданные по моделям ---
    models_meta: Dict[str, Dict[str, Any]] = {}
    for art_key, pair in mapping.items():
        mname = pair.get("model")
        if mname and mname in namespace and not inspect.isclass(namespace[mname]):
            models_meta[mname] = _model_info(namespace[mname])

    # --- 3️⃣ Артефакты (фигуры) ---
    if artifacts is None:
        fm = FigureManager()
        artifacts = fm.capture_current_figures()
    else:
        normalized: List[Artifact] = []
        for a in artifacts:
            if isinstance(a, Artifact):
                normalized.append(a)
            elif isinstance(a, dict):
                try:
                    normalized.append(Artifact(**a))
                except Exception:
                    pass
        artifacts = normalized

    # Привязываем артефакты к моделям
    for art in artifacts:
        link = mapping.get(art.name)
        if link:
            art.meta = {"model": link.get("model"), "data": link.get("data")}

    # --- 4️⃣ Сбор метрик ---
    metrics: Dict[str, Metric] = {}
    for k, v in namespace.items():
        if k.startswith("_"):
            continue

        src = lineage_map.get(k)
        model_name = src.get("model").__class__.__name__ if src and "model" in src else None

        # Если это Metric
        if isinstance(v, Metric):
            key = f"{model_name}/{v.name}" if model_name else v.name
            metrics[key] = v
            continue

        # Если скаляр
        if isinstance(v, (int, float)):
            key = f"{model_name}/{k}" if model_name else k
            metrics[key] = Metric(name=k, value=float(v))
            continue

        # Словарь со скалярами
        if isinstance(v, dict) and v:
            if all(isinstance(x, (int, float)) for x in v.values()):
                for subk, subv in v.items():
                    key = f"{model_name}/{subk}" if model_name else f"{k}/{subk}"
                    metrics[key] = Metric(name=subk, value=float(subv))
                continue

    # --- 5️⃣ Группировка метрик по моделям ---
    grouped_metrics: Dict[str, List[Dict[str, Any]]] = {}
    for key, met in metrics.items():
        if "/" in key:
            model_name, _ = key.split("/", 1)
            grouped_metrics.setdefault(model_name, []).append({"key": key, "name": met.name, "value": met.value})
        else:
            if len(models_meta) == 1:
                sole = next(iter(models_meta.keys()))
                grouped_metrics.setdefault(sole, []).append({"key": key, "name": met.name, "value": met.value})
            else:
                grouped_metrics.setdefault("ungrouped", []).append({"key": key, "name": met.name, "value": met.value})

    # --- 6️⃣ Собираем Run ---
    run = Run(
        id=run_id,
        name=run_name,
        duration_s=duration_s,
        params={},
        metrics=metrics,
        series={},
        artifacts=artifacts,
        code=code,
        stdout=stdout,
        stderr=stderr,
        error=error,
        meta={"mapping": mapping, "models": models_meta, "grouped_metrics": grouped_metrics}
    )
    return run
