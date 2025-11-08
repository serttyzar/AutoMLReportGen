from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import time
from typing import List


class RuntimeCapture:
    def __enter__(self):
        self._stdout = StringIO()
        self._stderr = StringIO()
        self._start = time.time()
        self._ctx_out = redirect_stdout(self._stdout)
        self._ctx_err = redirect_stderr(self._stderr)
        self._ctx_out.__enter__()
        self._ctx_err.__enter__()
        self.artifacts: List = []
        return self

    def __exit__(self, exc_type, exc, tb):
        self._ctx_err.__exit__(exc_type, exc, tb)
        self._ctx_out.__exit__(exc_type, exc, tb)
        self.duration_s = time.time() - self._start
        self.stdout = self._stdout.getvalue()
        self.stderr = self._stderr.getvalue()
        self.error = None if exc is None else f"{exc_type.__name__}: {exc}"

        try:
            from .figures import FigureManager, _GLOBAL_FIG_BUFFER
            fm = FigureManager()
            arts_now = fm.capture_current_figures()
            all_arts = list({_a.path: _a for _a in (arts_now + _GLOBAL_FIG_BUFFER)}.values())
            self.artifacts = all_arts
        except Exception:
            self.artifacts = []
