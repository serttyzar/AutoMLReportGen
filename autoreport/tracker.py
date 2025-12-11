# autoreport/tracker.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
import uuid
import inspect
from .capture.figures import FigureManager
from .capture.runtime import RuntimeCapture
from .capture.lineage import build_lineage_from_code, classify_variables
from .core.models import Run, Artifact, Metric
from .capture.lineage import extract_plot_variable_mapping


def _model_info(obj: Any) -> Dict[str, Any]:
    """
    Получение информации о модели: тип и параметры (если доступны)
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
    """Создаёт Run с AST-based lineage tracking."""
    
    run_id = uuid.uuid4().hex[:10]
    
    # 1. AST-анализ: строим граф зависимостей
    graph = build_lineage_from_code(code)
    var_to_model = classify_variables(namespace, graph)
    
    # 2. Находим модели
    models = {k: v for k, v in namespace.items() 
              if hasattr(v, "predict") and not inspect.isclass(v) and not k.startswith("_")}
    
    models_meta: Dict[str, Dict[str, Any]] = {}
    for mname, mobj in models.items():
        models_meta[mname] = _model_info(mobj)
    
    # 3. Обработка артефактов
    if artifacts is None:
        from .capture.figures import FigureManager, _GLOBAL_FIG_BUFFER
        fm = FigureManager()
        arts_now = fm.capture_current_figures()
        all_arts = list({a.path: a for a in (arts_now + _GLOBAL_FIG_BUFFER)}.values())
        artifacts = all_arts
        _GLOBAL_FIG_BUFFER.clear()  # КРИТИЧНО!
    else:
        normalized = []
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
    plot_to_model = extract_plot_variable_mapping(code, graph)
    
    for art in artifacts:
        if art.kind == "figure":
            # Извлекаем номер из имени: auto_1 -> 1 или figure_1 -> 1
            try:
                if art.name.startswith("auto_") or art.name.startswith("figure_"):
                    plot_idx = int(art.name.split("_")[1])
                    model_owner = plot_to_model.get(plot_idx)
                    if model_owner:
                        art.meta = {"model": model_owner}
                    else:
                        # Fallback: если AST не нашел - ставим ungrouped
                        art.meta = {"model": "ungrouped"}
                else:
                    # Если имя не соответствует шаблону - ungrouped
                    art.meta = {"model": "ungrouped"}
            except (ValueError, IndexError):
                art.meta = {"model": "ungrouped"}
    
    # 4. Группировка метрик через AST-граф
    metrics: Dict[str, Metric] = {}
    grouped_metrics: Dict[str, List[Dict[str, Any]]] = {}
    
    for var_name, val in namespace.items():
        if var_name.startswith("_"):
            continue
            
        model_owner = var_to_model.get(var_name, "ungrouped")
        
        if isinstance(val, (int, float)):
            metrics[var_name] = Metric(name=var_name, value=float(val))
            grouped_metrics.setdefault(model_owner, []).append({
                "key": var_name, "name": var_name, "value": float(val)
            })
            
        elif isinstance(val, dict) and val:
            if all(isinstance(x, (int, float)) for x in val.values()):
                for subk, subv in val.items():
                    full_key = f"{var_name}/{subk}"
                    metrics[full_key] = Metric(name=subk, value=float(subv))
                    grouped_metrics.setdefault(model_owner, []).append({
                        "key": full_key, "name": subk, "value": float(subv)
                    })
    
    # 5. Собираем Run
    run = Run(
        id=run_id, name=run_name, duration_s=duration_s, params={},
        metrics=metrics, series={}, artifacts=artifacts,
        code=code, stdout=stdout, stderr=stderr, error=error,
        meta={
            "models": models_meta,
            "grouped_metrics": grouped_metrics,
            "lineage_graph": {k: list(v.assigned_from) for k, v in graph.nodes.items()}
        }
    )
    return run
