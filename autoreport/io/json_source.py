from __future__ import annotations
from pathlib import Path
from typing import List
import json
from ..core.models import Run, ExperimentSet

def load_experiment_set(export_dir: Path) -> ExperimentSet:
    runs: List[Run] = []
    for run_dir in export_dir.glob("*"):
        run_json = run_dir / "run.json"
        if run_json.exists():
            data = json.loads(run_json.read_text(encoding="utf-8"))
            runs.append(Run(**data))
    return ExperimentSet(runs=runs)

def save_run(run: Run, export_dir: Path) -> Path:
    run_dir = export_dir / run.id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "run.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")
    return run_dir