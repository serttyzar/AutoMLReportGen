from pathlib import Path
from datetime import datetime
from jinja2 import Environment, PackageLoader, select_autoescape, FileSystemLoader
from autoreport.tracker import Experiment
import json, shutil, os

_ENV = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parent / "templates"),
    autoescape=select_autoescape()
)

def render_report(exp: Experiment, template: str = "simple") -> Path:
    tpl = _ENV.get_template(f"{template}.md.j2")
    md_text = tpl.render(
        exp=exp,
        now=datetime.now().strftime("%d.%m.%Y %H:%M")
    )

    out_dir = Path.cwd() / "autoreports"
    out_dir.mkdir(exist_ok=True)
    md_path = out_dir / f"{exp.run_id}.md"
    md_path.write_text(md_text, encoding="utf-8")

    if exp.figures:
        fig_dir = out_dir / f"{exp.run_id}_figs"
        fig_dir.mkdir(exist_ok=True)
        for f in exp.figures:
            shutil.copy2(f, fig_dir / Path(f).name)

    return md_path