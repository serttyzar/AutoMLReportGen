from IPython.core.magic import Magics, magics_class, line_cell_magic
from IPython import get_ipython
from argparse import ArgumentParser
import textwrap
from pathlib import Path
from .capture.runtime import RuntimeCapture
from .tracker import run_experiment
from .io.json_source import save_run
from .rendering.renderer import render_report_with_bundle
import sys
           
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
        
        # 🔧 ИСПРАВЛЕНИЕ: Защита от пустой ячейки
        if not code_cell.strip():
            code_cell = "# Генерация отчёта по всему ноутбуку"
        
        with RuntimeCapture() as rc:
            exec(code_cell, user_ns)

        # Собираем всю историю In[] из ноутбука
        try:
            inputs = getattr(ipy, 'user_ns', {}).get('In', None) or ipy.user_ns.get('In', [])
            if inputs and len(inputs) > 1:
                full_code = "\n\n# === Cell {} ===\n".join(
                    f"{i}\n{str(cell)}" for i, cell in enumerate(inputs[1:], 1)
                )
            else:
                full_code = code_cell
            sys.__stdout__.write(full_code + "\n")
        except Exception:
            full_code = code_cell  # fallback
        sys.__stdout__.write('wqefwef' + "\n")
        # Legacy переменные y_* → y_*_main
        for kind in ("true", "pred", "prob"):
            src = f"y_{kind}"
            dst = f"y_{kind}_{args.label}"
            if src in user_ns and dst not in user_ns:
                user_ns[dst] = user_ns[src]

        run = run_experiment(
            code=full_code, namespace=user_ns, run_name=args.name,
            stdout=rc.stdout, stderr=rc.stderr, error=rc.error, duration_s=rc.duration_s
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
