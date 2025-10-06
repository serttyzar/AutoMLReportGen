import hashlib
from pathlib import Path
from typing import Optional

def sha256_file(path: Path) -> Optional[str]:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def human_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"

def normalize_context(context: dict) -> dict:
    run = context.get("run")
    if run and "artifacts" in run:
        for art in run["artifacts"]:
            if isinstance(art.get("path"), Path):
                art["path"] = art["path"].as_posix()
    return context