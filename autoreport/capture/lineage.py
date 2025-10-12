# autoreport/capture/lineage.py
"""
Lineage Tracker — отслеживает происхождение данных (моделей, метрик, графиков)
для sklearn и PyTorch. Автоматически связывает артефакты с их моделью-источником.
"""

from __future__ import annotations
import functools
from typing import Any, Dict

# --- Глобальное хранилище lineage ---
_LINEAGE: Dict[int, Dict[str, Any]] = {}


# ==============================================================
#                      ОСНОВНЫЕ УТИЛИТЫ
# ==============================================================

def tag(obj: Any, source: Dict[str, Any]):
    """Присвоить объекту lineage-метку."""
    try:
        _LINEAGE[id(obj)] = source
        setattr(obj, "__lineage__", source)
    except Exception:
        # torch.Tensor не поддерживает setattr — пропускаем
        pass


def get(obj: Any) -> Dict[str, Any] | None:
    """Получить lineage-метку (если есть)."""
    if obj is None:
        return None
    if hasattr(obj, "__lineage__"):
        return getattr(obj, "__lineage__")
    return _LINEAGE.get(id(obj))


def inherit_result(fn):
    """Декоратор: переносит lineage от аргументов в результат."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        result = fn(*args, **kwargs)
        for a in list(args) + list(kwargs.values()):
            src = get(a)
            if src:
                tag(result, src)
                break
        return result
    return wrapper


# ==============================================================
#                   SKLEARN PATCHING
# ==============================================================

def _patch_sklearn():
    try:
        from sklearn.base import ClassifierMixin, RegressorMixin, ClusterMixin, TransformerMixin
        from sklearn import metrics as skmetrics
    except ImportError:
        return

    def _patch_predict_like(cls):
        if getattr(cls, "_autoreport_patched", False):
            return

        if hasattr(cls, "predict"):
            orig_predict = cls.predict

            def _patched_predict(self, X, *a, **kw):
                y_pred = orig_predict(self, X, *a, **kw)
                tag(y_pred, {"type": "prediction", "model": self})
                return y_pred

            cls.predict = _patched_predict

        if hasattr(cls, "score"):
            orig_score = cls.score

            def _patched_score(self, X, y, *a, **kw):
                res = orig_score(self, X, y, *a, **kw)
                tag(res, {"type": "score", "model": self})
                return res

            cls.score = _patched_score

        if hasattr(cls, "transform"):
            orig_transform = cls.transform

            def _patched_transform(self, X, *a, **kw):
                X_t = orig_transform(self, X, *a, **kw)
                tag(X_t, {"type": "transform", "model": self})
                return X_t

            cls.transform = _patched_transform

        cls._autoreport_patched = True

    # Пропатчить миксины
    for mixin in [ClassifierMixin, RegressorMixin, ClusterMixin, TransformerMixin]:
        _patch_predict_like(mixin)

    # Пропатчить метрики
    for name in dir(skmetrics):
        fn = getattr(skmetrics, name)
        if callable(fn) and not name.startswith("_"):
            try:
                setattr(skmetrics, name, inherit_result(fn))
            except Exception:
                pass


# ==============================================================
#                   PYTORCH PATCHING
# ==============================================================

def _patch_pytorch():
    try:
        import torch.nn as nn
    except ImportError:
        return

    if getattr(nn.Module, "_autoreport_patched", False):
        return

    orig_call = nn.Module.__call__

    def wrapped_call(self, *args, **kwargs):
        out = orig_call(self, *args, **kwargs)
        # torch.Tensor не поддерживает setattr, используем _LINEAGE
        try:
            _LINEAGE[id(out)] = {"type": "prediction", "model": self}
        except Exception:
            pass
        return out

    nn.Module.__call__ = wrapped_call
    nn.Module._autoreport_patched = True


# ==============================================================
#                   MATPLOTLIB PATCHING
# ==============================================================

def _patch_matplotlib():
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return

    plot_fns = ["plot", "scatter", "bar", "imshow", "hist"]

    for name in plot_fns:
        if hasattr(plt, name):
            orig_fn = getattr(plt, name)

            @functools.wraps(orig_fn)
            def make_wrapper(fn):
                def wrapped(*args, **kwargs):
                    res = fn(*args, **kwargs)
                    for a in list(args) + list(kwargs.values()):
                        src = get(a)
                        if src:
                            try:
                                tag(plt.gcf(), src)
                            except Exception:
                                pass
                            break
                    return res
                return wrapped

            setattr(plt, name, make_wrapper(orig_fn))


# ==============================================================
#                   LINEAGE COLLECTOR
# ==============================================================

def collect_namespace_lineage(namespace: dict) -> Dict[str, Dict[str, Any]]:
    """
    Возвращает mapping:
      { var_name: {"type": ..., "model": ...} }
    для всех объектов в namespace, имеющих lineage.
    """
    result = {}
    for name, val in namespace.items():
        src = get(val)
        if src:
            result[name] = src
    return result


# ==============================================================
#                   AUTO-ACTIVATION
# ==============================================================

_patch_sklearn()
_patch_pytorch()
_patch_matplotlib()

_activated = True
