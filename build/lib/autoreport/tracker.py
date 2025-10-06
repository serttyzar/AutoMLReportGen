from __future__ import annotations
from typing import Dict, Any
import uuid
from pathlib import Path
from .capture.figures import FigureManager
from .capture.runtime import RuntimeCapture
from .capture.variables import discover_models_and_data
from .core.models import Run, Artifact

def run_experiment(code: str, namespace: Dict[str, Any], run_name: str,
                   stdout: str, stderr: str, error: str | None, duration_s: float) -> Run:
    run_id = uuid.uuid4().hex[:10]

    # Захват пользовательских объектов моделей и данных
    mapping = discover_models_and_data(namespace)

    # Захват всех текущих фигур
    figman = FigureManager()
    artifacts = figman.capture_current_figures()

    # Привязываем каждый артефакт к модели/данным, если возможно
    for art in artifacts:
        # art — pydantic Artifact
        link = mapping.get(art.name.split('.')[0])
        if link:
            art.meta = {"model": link["model"], "data": link["data"]}

    run = Run(
        id=run_id,
        name=run_name,
        duration_s=duration_s,
        params={},  # оставляем под user
        metrics={},  # убрали автоматические метрики
        series={},
        artifacts=artifacts,
        code=code,
        stdout=stdout,
        stderr=stderr,
        error=error,
        meta={"mapping": mapping}
    )
    return run
