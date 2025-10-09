# autoreport/capture/variables.py
from typing import Dict, Any
import inspect
import re

def discover_models_and_data(namespace: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Ищем объекты-модели (Estimator-подобные) и массивы данных X, y.
    Возвращаем mapping: {artifact_name: {"model": model_var, "data": data_var}}
    """
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
