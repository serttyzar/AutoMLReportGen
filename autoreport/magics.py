from IPython.core.magic import Magics, magics_class, line_cell_magic
from IPython import get_ipython
from argparse import ArgumentParser
import textwrap
from pathlib import Path
from .capture.runtime import RuntimeCapture
from .tracker import run_experiment
from .io.json_source import save_run
from .rendering.renderer import render_html


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
        code = textwrap.dedent(cell or "")

        with RuntimeCapture() as rc:
            exec(code, user_ns)

        for kind in ("true", "pred", "prob"):
            src = f"y_{kind}"
            dst = f"y_{kind}_{args.label}"
            if src in user_ns and dst not in user_ns:
                user_ns[dst] = user_ns[src]

        run = run_experiment(
            code=code, namespace=user_ns, run_name=args.name,
            stdout=rc.stdout, stderr=rc.stderr, error=rc.error, duration_s=rc.duration_s
        )

        export_dir = Path("export")
        save_run(run, export_dir)

        template_dir = Path(__file__).resolve().parent / "rendering" / "templates"
        context = {"run": run.model_dump()}
        out_path = Path(args.outdir) / run.id / "index.html"
        render_html(template_dir, args.template, context, out_path)
        print(f"Report ready: {out_path}")

# ВНЕ класса:
def load_ipython_extension(ip):
    ip.register_magics(AutoReportMagics)
