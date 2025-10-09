# autoreport/capture/figures.py
from __future__ import annotations
from pathlib import Path
from typing import List
import os
import matplotlib.pyplot as plt
import matplotlib.figure
from ..core.utils import sha256_file
from ..core.models import Artifact

_GLOBAL_FIG_BUFFER: List[Artifact] = []


class FigureManager:
    """
    Менеджер для захвата фигур matplotlib. Работает и в Jupyter, и в обычных скриптах.
    """

    def __init__(self, cache_dir: Path = Path(".autoreport_cache")):
        self.cache_dir = cache_dir
        (self.cache_dir / "artifacts").mkdir(parents=True, exist_ok=True)

    def _save_fig(self, fig, name: str, image_format: str = "png", dpi: int = 150) -> Artifact | None:
        tmp_path = self.cache_dir / "artifacts" / f"tmp_{name}.{image_format}"
        fig.savefig(tmp_path, dpi=dpi, bbox_inches="tight")

        sha = sha256_file(tmp_path)
        if sha is None:
            try:
                tmp_path.unlink(missing_ok=True)
            except Exception:
                pass
            return None

        subdir = self.cache_dir / "artifacts" / sha[:2]
        subdir.mkdir(parents=True, exist_ok=True)
        final_path = subdir / f"{sha}.{image_format}"

        if not final_path.exists():
            os.replace(tmp_path, final_path)
        else:
            tmp_path.unlink(missing_ok=True)

        return Artifact(
            name=name,
            path=str(final_path.as_posix()),
            kind="figure",
            sha256=sha,
            size_bytes=final_path.stat().st_size
        )

    def capture_current_figures(self, image_format: str = "png", dpi: int = 150) -> List[Artifact]:
        artifacts: List[Artifact] = []
        for i, num in enumerate(plt.get_fignums(), start=1):
            fig = plt.figure(num)
            art = self._save_fig(fig, f"figure_{i}", image_format, dpi)
            if art:
                artifacts.append(art)
        return artifacts


# --- 1️⃣ Monkey-patch: display hook для Jupyter --- #
try:
    import builtins
    import IPython.display as ipd

    _original_display = ipd.display

    def _patched_display(*objs, **kwargs):
        fm = FigureManager()
        for obj in objs:
            if isinstance(obj, matplotlib.figure.Figure):
                art = fm._save_fig(obj, f"auto_{len(_GLOBAL_FIG_BUFFER)+1}")
                if art:
                    _GLOBAL_FIG_BUFFER.append(art)
        return _original_display(*objs, **kwargs)

    ipd.display = _patched_display

except Exception:
    pass


# --- 2️⃣ Monkey-patch: plt.show() для не-Jupyter --- #
import matplotlib

_original_show = matplotlib.pyplot.show


def _patched_show(*args, **kwargs):
    fm = FigureManager()
    arts = fm.capture_current_figures()
    if arts:
        _GLOBAL_FIG_BUFFER.extend(arts)
    return _original_show(*args, **kwargs)


matplotlib.pyplot.show = _patched_show
