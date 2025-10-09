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

def _model_info(obj: Any) -> Dict[str, Any]:
    """
    Попытка получить информацию о модели: тип и параметры (если доступны).
    """
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
    Создаёт Run. Если 'artifacts' переданы (например, из RuntimeCapture), использует их.
    Иначе попытается сам захватить текущие фигуры.
    Также собирает модели + метрики и группирует метрики по моделям.
    """
    run_id = uuid.uuid4().hex[:10]

    # Захват пользовательских объектов моделей и данных (mapping keyed by figure_N)
    mapping = discover_models_and_data(namespace)

    # Собираем метаданные по моделям (type + params)
    models_meta: Dict[str, Dict[str, Any]] = {}
    for art_key, pair in mapping.items():
        mname = pair.get("model")
        if mname and mname in namespace and not inspect.isclass(namespace[mname]):
            models_meta[mname] = _model_info(namespace[mname])

    # Собираем артефакты (figures). Если передали извне — используем их, иначе захватим сами.
    if artifacts is None:
        figman = FigureManager()
        artifacts = figman.capture_current_figures()
    else:
        # нормализуем — приводим dict -> Artifact при необходимости
        normalized: List[Artifact] = []
        for a in artifacts:
            if isinstance(a, Artifact):
                normalized.append(a)
            elif isinstance(a, dict):
                try:
                    normalized.append(Artifact(**a))
                except Exception:
                    # если не подошло — пропускаем
                    pass
        artifacts = normalized

    # Привязываем каждый артефакт к модели/данным, если возможно
    for art in artifacts:
        link = mapping.get(art.name)
        if link:
            art.meta = {"model": link.get("model"), "data": link.get("data")}

    # Автоматический сбор метрик из namespace (эвристики):
    # - скаляры (int/float)
    # - dict со скалярными значениями
    metrics: Dict[str, Metric] = {}
    for k, v in namespace.items():
        if k.startswith("_"):
            continue
        # pydantic Metric
        try:
            if isinstance(v, Metric):
                metrics[k] = v
                continue
        except Exception:
            pass

        # скаляры
        if isinstance(v, (int, float)):
            matched_model = next((m for m in models_meta.keys() if m in k), None)
            short = k.replace(matched_model, "").strip("_") if matched_model else k
            key = f"{matched_model}/{short or k}" if matched_model else k
            metrics[key] = Metric(name=short or k, value=float(v))
            continue

        # словари со скалярными значениями
        if isinstance(v, dict) and v:
            if all(isinstance(x, (int, float)) for x in v.values()):
                matched_model = next((m for m in models_meta.keys() if m in k), None)
                for subk, subv in v.items():
                    if matched_model:
                        key = f"{matched_model}/{subk}"
                    else:
                        key = f"{k}/{subk}"
                    metrics[key] = Metric(name=subk, value=float(subv))
                continue

    # Группируем метрики по моделям (упростит шаблон)
    grouped_metrics: Dict[str, List[Dict[str, Any]]] = {}
    for key, met in metrics.items():
        if "/" in key:
            model_name, _ = key.split("/", 1)
            grouped_metrics.setdefault(model_name, []).append({"key": key, "name": met.name, "value": met.value})
        else:
            # если модель лишь одна — приписывать к ней
            if len(models_meta) == 1:
                sole = next(iter(models_meta.keys()))
                grouped_metrics.setdefault(sole, []).append({"key": key, "name": met.name, "value": met.value})
            else:
                grouped_metrics.setdefault("ungrouped", []).append({"key": key, "name": met.name, "value": met.value})

    run = Run(
        id=run_id,
        name=run_name,
        duration_s=duration_s,
        params={},  # оставляем под user
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
