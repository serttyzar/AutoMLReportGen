from IPython.core.magic import Magics, magics_class, line_cell_magic
from IPython import get_ipython
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import builtins, types, ast, tempfile, sys, textwrap, traceback, uuid, time
import argparse
from autoreport.tracker import run_experiment
from autoreport.report import render_report


@magics_class
class AutoReportMagics(Magics):
    """
    %%autoreport — магическая команда для auto-tracking.
    Пример использования:

        %%autotreport --name "CatBoost one-hot" --template research
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
    """

    @line_cell_magic
    def autoreport(self, line, cell=None):
        parser = argparse.ArgumentParser(prog="%%autoreport", add_help=False)
        parser.add_argument("--name", default="SmartRun")
        parser.add_argument("--template", default="simple")
        parser.add_argument("--silent", action="store_true")
        args, _ = parser.parse_known_args(line.split())

        stdout_buf, stderr_buf = StringIO(), StringIO()
        ipy = get_ipython()

        started = time.time()

        user_ns = ipy.user_ns
        cell_code = textwrap.dedent(cell or "")
        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                exec(cell_code, user_ns)
            exec_error = None
        except Exception as exc:
            exec_error = traceback.format_exc()

        duration = time.time() - started

        try:
            tree = ast.parse(cell_code)
        except SyntaxError:
            tree = None

        exp = run_experiment(
            code=cell_code,
            code_ast=tree,
            namespace=user_ns,
            run_name=args.name,
            exec_stdout=stdout_buf.getvalue(),
            exec_stderr=stderr_buf.getvalue(),
            exec_error=exec_error,
            duration_s=duration
        )


        md_path = render_report(exp, template=args.template)
        if not args.silent:
            print(f"Report ready: {md_path}")

        if stdout_buf.getvalue():
            print(stdout_buf.getvalue(), end="")
        if stderr_buf.getvalue():
            print(stderr_buf.getvalue(), file=sys.stderr)
 
        if exec_error:
            raise RuntimeError("AutoReport: ошибка внутри ячейки, см. отчёт")