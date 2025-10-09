from __future__ import annotations
from pathlib import Path
from typing import List
import matplotlib.pyplot as plt
import os
from ..core.utils import sha256_file
from ..core.models import Artifact
import io

class FigureManager:
    
    def __init__(self, cache_dir: Path = Path(".autoreport_cache")):
        self.cache_dir = cache_dir
        (self.cache_dir / "artifacts").mkdir(parents=True, exist_ok=True)
        
    def capture_current_figures(self, image_format: str = "png", dpi: int = 200) -> List[Artifact]:
        artifacts: List[Artifact] = []
        for num in plt.get_fignums():
            fig = plt.figure(num)
            tmp_path = self.cache_dir / "artifacts" / f"tmp_{num}.{image_format}"
            fig.savefig(tmp_path, dpi=dpi, bbox_inches="tight")
            sha = sha256_file(tmp_path)
            if sha is None:
                try:
                    tmp_path.unlink(missing_ok=True)
                except Exception:
                    pass
                continue
            subdir = self.cache_dir / "artifacts" / sha[:2]
            subdir.mkdir(parents=True, exist_ok=True)
            final_path = subdir / f"{sha}.{image_format}"
            if not final_path.exists():
                try:
                    os.replace(tmp_path, final_path)
                except Exception:
                    # fallback to copy
                    import shutil
                    shutil.copy2(tmp_path, final_path)
                    tmp_path.unlink(missing_ok=True)
            else:
                tmp_path.unlink(missing_ok=True)
            artifacts.append(Artifact(
                name=f"figure_{num}",
                path=str(final_path.as_posix()),
                kind="figure",
                sha256=sha,
                size_bytes=final_path.stat().st_size
            ))
        return artifacts
    

    def capture_all_figures() -> list[Artifact]:
        arts = []
        for num in plt.get_fignums():
            fig = plt.figure(num)
            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            buf.seek(0)
            arts.append(Artifact.from_image(buf.getvalue(), name=f"figure_{num}"))
        return arts