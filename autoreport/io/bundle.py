from __future__ import annotations
from pathlib import Path
import shutil
from typing import List


def assemble_bundle(report_dir: Path, artifacts: list, mode: str = "copy"):
    assets = report_dir / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    updated = []
    for art in artifacts:
        # art может быть pydantic-моделью или dict — приведём к dict
        art_dict = art if isinstance(art, dict) else art.model_dump()
        src = Path(art_dict["path"])
        dst = assets / src.name

        if mode == "copy":
            if not dst.exists():
                shutil.copy2(src, dst)
        elif mode == "symlink":
            if not dst.exists():
                try:
                    dst.symlink_to(src.resolve())
                except Exception:
                    shutil.copy2(src, dst)
        else:
            if not dst.exists():
                shutil.copy2(src, dst)
        art_dict["path"] = str(Path("assets") / src.name)
        updated.append(art_dict)
    return updated

