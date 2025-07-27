from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import inspect, numbers, itertools, uuid, hashlib, json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, mean_squared_error, r2_score
)
import pandas as pd
import tempfile

@dataclass
class Experiment:
    run_id: str
    run_name: str
    code: str
    stdout: str
    stderr: str
    error: Optional[str]
    duration_s: float
    metrics: Dict[str, float] = field(default_factory=dict)
    figures: List[Path] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)


def _hash_arr(arr):
    try:
        return hashlib.md5(np.asarray(arr).tobytes()).hexdigest()
    except Exception:
        return None


def _auto_metrics(namespace) -> Dict[str, float]:
    vars_ = {k: v for k, v in namespace.items()
             if isinstance(v, (list, tuple, np.ndarray, pd.Series))}
    keys = list(vars_.keys())

    found = {}
    for a, b in itertools.combinations(keys, 2):
        if a.endswith("_true") and b.endswith("_pred") and len(vars_[a]) == len(vars_[b]):
            found[a[:-5]] = (vars_[a], vars_[b])
        if b.endswith("_true") and a.endswith("_pred") and len(vars_[a]) == len(vars_[b]):
            found[b[:-5]] = (vars_[b], vars_[a])

    results = {}
    for label, (y_t, y_p) in found.items():
        y_t, y_p = np.asarray(y_t), np.asarray(y_p)
        uniq = np.unique(y_t)
        if y_t.dtype.kind in "ifu" and len(uniq) > 10:        # регрессия
            results[f"{label}_mse"] = mean_squared_error(y_t, y_p)
            results[f"{label}_r2"] = r2_score(y_t, y_p)
        else:                                                 # классификация
            results[f"{label}_acc"] = accuracy_score(y_t, y_p)
            results[f"{label}_prec"] = precision_score(y_t, y_p, average="weighted", zero_division=0)
            results[f"{label}_rec"] = recall_score(y_t, y_p, average="weighted", zero_division=0)
            results[f"{label}_f1"] = f1_score(y_t, y_p, average="weighted", zero_division=0)
            if len(uniq) == 2:
                try:
                    results[f"{label}_auc"] = roc_auc_score(y_t, y_p)
                except ValueError:
                    pass
    return results


def _capture_figures(tmpdir: Path) -> List[Path]:
    paths = []
    for num in plt.get_fignums():
        fig = plt.figure(num)
        fname = tmpdir / f"figure_{num}.png"
        fig.savefig(fname, dpi=300, bbox_inches="tight")
        paths.append(fname)
    return paths


def run_experiment(
    code: str,
    code_ast,
    namespace: dict,
    run_name: str,
    exec_stdout: str,
    exec_stderr: str,
    exec_error: str,
    duration_s: float
) -> Experiment:
    run_id = uuid.uuid4().hex[:10]

    metrics = _auto_metrics(namespace)

    tmpdir = Path(tempfile.mkdtemp(prefix="sr_fig_"))
    figs = _capture_figures(tmpdir)

    exp = Experiment(
        run_id=run_id,
        run_name=run_name,
        code=code,
        stdout=exec_stdout,
        stderr=exec_stderr,
        error=exec_error,
        duration_s=duration_s,
        metrics=metrics,
        figures=figs,
        extras={}
    )
    return exp
