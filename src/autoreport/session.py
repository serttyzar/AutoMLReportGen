from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
import threading
from datetime import datetime
import time
import uuid
from pathlib import Path

from .tracker import Experiment
from .capture.figures import FigureManager


@dataclass
class CellExecution:
    cell_id: str
    code: str
    outputs: str
    errors: Optional[str]
    figures: List[Path]
    duration: float
    execution_order: int = 0


class NotebookSession:
    "Manage all cells in notebook"
    _active_sessions: Dict[str, 'NotebookSession'] = {}
    _lock = threading.Lock()

    def __init__(self, notebook_id: str = None, 
                 experiment_name: str = None):
        self.notebook_id = notebook_id
        self.experiment_name = experiment_name or f"Notebook_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.experiment = Experiment(
            run_id=str(uuid.uuid4()),
            run_name=self.experiment_name,
            code="",
            stdout="",
            stderr="", 
            error=None,
            duration_s=0.0
        )
        
        self.cell_executions: List[CellExecution] = []
        self.execution_cnt = 0

        self.figure_manager = FigureManager()

        self.total_duration = 0.0
        self.session_start_time = time.time()

        with NotebookSession._lock:
            NotebookSession._active_sessions[self.notebook_id] = self
        
    @classmethod
    def get_session(cls, notebook_id: str = None, 
                    experiment_name: str = None
                    ) -> 'NotebookSession':
        """Get or create session if not exist"""
        if notebook_id is None:
            try:
                from IPython import get_ipython
                ip = get_ipython()
                if ip and hasattr(ip, 'kernel'):
                    notebook_id = getattr(ip.kernel, 'session_id', str(uuid.uuid4()))
                else:
                    notebook_id = str(uuid.uuid4())
            except:
                notebook_id = str(uuid.uuid4())
        with cls._lock:
            if notebook_id in cls._active_sessions:
                return cls._active_sessions[notebook_id]
            return cls(notebook_id, experiment_name)
    
    def execute_cell(self, code: str, 
                        cell_context: Dict[str, Any] = None
                        ) -> CellExecution:
        """Execute and analyze cell"""
        self.execution_cnt += 1
        cell_id = f"cell_{self.execution_counter}"
        start_time = time.time()

        from contextlib import redirect_stdout, redirect_stderr
        from io import StringIO
        import textwrap
        import traceback
        
        stdout_buf, stderr_buf = StringIO(), StringIO()
        exec_error = None
        
        try:
            from IPython import get_ipython
            user_ns = get_ipython().user_ns
            
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                exec(textwrap.dedent(code), user_ns)
        except Exception:
            exec_error = traceback.format_exc()
        
        duration = time.time() - start_time
        self.total_duration += duration
        
        cell_execution = CellExecution(
            cell_id=cell_id,
            code=code,
            outputs=stdout_buf.getvalue(),
            errors=exec_error,
            duration=duration,
            execution_order=self.execution_counter
        )

        # МЕСТО ДЛЯ АНАЛИЗА КОДА и МЛ МОДЕЛИ

        captured_figures = self.figure_manager.capture_cur_figures()
        cell_execution.figures = captured_figures
        
        self._update_experiment(cell_execution)
        
        self.cell_executions.append(cell_execution)
        
        return cell_execution
    
    def _update_experiment(self, cell_execution: CellExecution):
        """Update experiment with new cell"""
        self.experiment.code += f'\n# Cell {cell_execution.execution_order}\n{cell_execution.code}\n'
        if cell_execution.outputs:
            self.experiment.stdout += f'\n# Cell {cell_execution.execution_order} Output:\n{cell_execution.outputs}\n'

        if cell_execution.errors:
            self.experiment.stderr += f"\n# Cell {cell_execution.execution_order} Errors:\n{cell_execution.errors}\n"

        self.experiment.figures.extend(cell_execution.figures)

        self.experiment.duration_s = self.total_duration
    

    def get_experiment_summary(self) -> Dict[str, Any]:
        pass

    def finalize_experiment(self) -> Experiment:
        pass

    def clear_session(self):
        with NotebookSession._lock:
            if self.notebook_id in NotebookSession._active_sessions:
                del NotebookSession._active_sessions[self.notebook_id]
        
        self.figure_manager.cleanup()


def get_session() -> NotebookSession:
    return NotebookSession.get_session()
        