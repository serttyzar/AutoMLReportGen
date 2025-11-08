from typing import Dict, Any
import inspect
import matplotlib.pyplot as plt

def discover_models_and_data(namespace: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    """
    Ищем объекты-модели (экземпляры с .predict, НЕ классы) и массивы данных X, y.
    Возвращаем mapping: { "figure_<idx>": {"model": model_var, "data": data_var or None} }

    Эвристика:
    - не берём классы (inspect.isclass)
    - сопоставляем моделям последовательные номера фигур (figure_1, figure_2, ...)
      — это согласовано с FigureManager (так нам проще гарантировать связывание)
    - ищем data-переменную по шаблонам: <model>_X, <model>_y, X, y, X_train, y_train...
    """
    models = [(k, v) for k, v in namespace.items() if hasattr(v, "predict") and not inspect.isclass(v)]
    data_candidates = [k for k, v in namespace.items() if not hasattr(v, "predict") and not k.startswith("__")]

    mapping: Dict[str, Dict[str, str]] = {}
    # используем последовательность моделей (1..n) — это соответствует именованию фигур figure_1..N
    for idx, (mname, mobj) in enumerate(models):
        art_key = f"figure_{idx+1}"
        candidates = [
            f"{mname}_X", f"{mname}_y", f"{mname}_data", f"{mname}_X_train", f"{mname}_y_train"
        ] + ["X", "y", "X_train", "y_train", "X_test", "y_test"]

        data_found = None
        for c in candidates:
            if c in namespace and not hasattr(namespace[c], "predict"):
                data_found = c
                break

        if data_found is None:
            for dn in data_candidates:
                v = namespace[dn]
                if hasattr(v, "__len__") and not isinstance(v, (str, bytes)):
                    data_found = dn
                    break

        mapping[art_key] = {"model": mname, "data": data_found}

    return mapping
