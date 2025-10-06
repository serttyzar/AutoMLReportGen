from __future__ import annotations
from typing import Any, Dict, Optional
from pathlib import Path
from .core.models import Run, Metric, Artifact
from .tracker import run_experiment

class Session:
    def __init__(self, name: str = "Session"):
        self.name = name
        self.namespace: Dict[str, Any] = {}
        self.params: Dict[str, Any] = {}

    def log_predictions(self, y_true, y_pred, y_prob=None, label: str = "main"):
        self.namespace[f"y_true_{label}"] = y_true
        self.namespace[f"y_pred_{label}"] = y_pred
        if y_prob is not None:
            self.namespace[f"y_prob_{label}"] = y_prob

    def log_params(self, params: Dict[str, Any]):
        self.params.update(params)

    def finalize(self, code: str = "# session", stdout: str = "", stderr: str = "", error: Optional[str] = None, duration_s: float = 0.0) -> Run:
        run = run_experiment(code=code, namespace=self.namespace, run_name=self.name, stdout=stdout, stderr=stderr, error=error, duration_s=duration_s)
        run.params = self.params
        return run

def get_session(name: str = "Session") -> Session:
    return Session(name=name)
