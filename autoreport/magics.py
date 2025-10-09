# autoreport/magics.py
from IPython.core.magic import Magics, magics_class, line_cell_magic
from IPython import get_ipython
from argparse import ArgumentParser
import textwrap
from pathlib import Path
import sys
import os

# Make imports robust for running from source
_this_dir = Path(__file__).resolve().parent
_project_root = _this_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

try:
    from autoreport.capture.runtime import RuntimeCapture
    from autoreport.tracker import run_experiment
    from autoreport.io.json_source import save_run
    from autoreport.rendering.renderer import render_report_with_bundle
except Exception:
    # fallback (rare)
    from .capture.runtime import RuntimeCapture  # type: ignore
    from .tracker import run_experiment  # type: ignore
    from .io.json_source import save_run  # type: ignore
    from .rendering.renderer import render_report_with_bundle  # type: ignore


@magics_class
class AutoReportMagics(Magics):
    @line_cell_magic
    def autoreport(self, line, cell=None):
        parser = ArgumentParser(prog="%%autoreport", add_help=False)
        parser.add_argument("--name", default="SmartRun")
        parser.add_argument("--template", default="default.html.j2")
        parser.add_argument("--outdir", default="reports")
        parser.add_argument("--label", default="main")
        args, _ = parser.parse_known_args(line.split())


        ipy = get_ipython()
        user_ns = ipy.user_ns
        code_cell = textwrap.dedent(cell or "")


        # Защита: если тело пустое, подложим комментарий (Jupyter не любит абсолютно пустые cell-magics)
        if not code_cell.strip():
            code_cell = "# full notebook"


        with RuntimeCapture() as rc:
            # Выполняем тело магии (если там есть код)
            if code_cell.strip() and not code_cell.strip().startswith("# full notebook"):
                exec(code_cell, user_ns)


        # Собираем всю историю In[] (текст ячеек) — это будет код в отчёте
        try:
            inputs = getattr(ipy, 'user_ns', {}).get('In', None) or ipy.user_ns.get('In', [])
            if inputs and len(inputs) > 1:
                # собираем все ячейки (пропускаем пустые)
                parts = []
                for i, c in enumerate(inputs[1:], 1):
                    if c and c.strip():
                        parts.append(f"# === Cell {i} ===\n{c}")
                full_code = "\n\n".join(parts) if parts else code_cell
            else:
                full_code = code_cell
        except Exception:
            full_code = code_cell

        # Передаём в run_experiment и — очень важно — отдаём артефакты, захваченные RuntimeCapture
        run = run_experiment(
            code=full_code, namespace=user_ns, run_name=args.name,
            stdout=rc.stdout, stderr=rc.stderr, error=rc.error, duration_s=rc.duration_s,
            artifacts=getattr(rc, "artifacts", None)
        )


        export_dir = Path("export")
        save_run(run, export_dir)


        template_dir = Path(__file__).resolve().parent / "rendering" / "templates"
        report_dir = Path(args.outdir) / run.id
        render_report_with_bundle(
        template_dir, args.template, {"run": run.model_dump()},
        report_dir=report_dir, bundle_mode="copy"
        )
        print(f"Report ready: {report_dir / 'index.html'}")

def load_ipython_extension(ip):
    ip.register_magics(AutoReportMagics)
