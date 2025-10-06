from __future__ import annotations
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from ..core.utils import normalize_context
from datetime import datetime
from ..io.bundle import assemble_bundle

def get_env(templates_dir: Path) -> Environment:
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"]),
        enable_async=False,
    )
    env.filters["pct"] = lambda x: f"{100*float(x):.2f}%"
    env.filters["fmt"] = lambda x: f"{float(x):.4f}"
    return env

def render_html(template_dir: Path, template_name: str, context: dict, out_path: Path) -> Path:
    env = get_env(template_dir)
    tpl = env.get_template(template_name)
    context = normalize_context(context)
    html = tpl.render(**context)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path

def render_report_with_bundle(template_dir: Path, template_name: str, context: dict,
                              report_dir: Path, bundle_mode: str = "copy") -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    ctx = normalize_context(context)
    ctx.setdefault("now", datetime.now().strftime("%d.%m.%Y %H:%M"))

    run = ctx.get("run", {})
    artifacts = run.get("artifacts", [])
    if isinstance(artifacts, list) and artifacts:
        updated = assemble_bundle(report_dir, artifacts, mode=bundle_mode)
        run = dict(run)
        run["artifacts"] = updated
        ctx["run"] = run

    out_path = report_dir / "index.html"
    return render_html(template_dir, template_name, ctx, out_path)