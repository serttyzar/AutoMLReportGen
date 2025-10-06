from typing import Dict, Any, Tuple, List
import numpy as np
from typing import Dict, Any
import inspect
import re

def discover_labels(namespace: Dict[str, Any]) -> List[str]:
    keys = list(namespace.keys())
    labels = set()
    for k in keys:
        if k.startswith("y_true_"):
            labels.add(k[len("y_true_"):])
        if k.startswith("y_pred_"):
            labels.add(k[len("y_pred_"):])
        if k.startswith("y_prob_"):
            labels.add(k[len("y_prob_"):])
    return sorted(labels)


def extract_predictions(namespace: Dict[str, Any]) -> Dict[str, Dict[str, np.ndarray]]:
    result: Dict[str, Dict[str, np.ndarray]] = {}
    labels = discover_labels(namespace)
    for lbl in labels:
        entry: Dict[str, np.ndarray] = {}
        for kind in ("true", "pred", "prob"):
            name = f"y_{kind}_{lbl}"
            if name in namespace:
                try:
                    arr = np.asarray(namespace[name])
                    entry[kind] = arr
                except Exception:
                    continue
        if entry:
            result[lbl] = entry
    return result


def discover_models_and_data(namespace: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    models = {k: v for k, v in namespace.items() if hasattr(v, 'predict')}
    data_vars = {k: v for k, v in namespace.items() if hasattr(v, '__len__') and not hasattr(v, 'predict')}
    mapping: Dict[str, Dict[str, str]] = {}
    # По имени фигуры (figure_N) сопоставлять по порядку model+data
    idx = 0
    for name in models:
        data_name = next(iter(data_vars), None)
        art_key = f"figure_{idx+1}"
        mapping[art_key] = {"model": name, "data": data_name}
        idx += 1
    return mapping
