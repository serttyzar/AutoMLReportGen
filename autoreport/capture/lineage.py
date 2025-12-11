"""
AST-based lineage tracker для автоматической привязки метрик и графиков к моделям.
Парсит код ноутбука и строит граф зависимостей переменных.
"""

from __future__ import annotations
import ast
from typing import Dict, Set, Optional, Any, List
from dataclasses import dataclass, field


@dataclass
class VarNode:
    """Узел графа зависимостей переменной."""
    name: str
    assigned_from: Set[str] = field(default_factory=set)
    method_call: Optional[str] = None
    parent_obj: Optional[str] = None


class DependencyGraph:
    """Граф зависимостей переменных в коде."""
    
    def __init__(self):
        self.nodes: Dict[str, VarNode] = {}
        
    def add_assignment(self, target: str, deps: Set[str], 
                      method: Optional[str] = None, parent: Optional[str] = None):
        """Регистрация присваивания."""
        if target not in self.nodes:
            self.nodes[target] = VarNode(target)
        self.nodes[target].assigned_from.update(deps)
        if method:
            self.nodes[target].method_call = method
        if parent:
            self.nodes[target].parent_obj = parent
            
    def get_origin_model(self, var_name: str) -> Optional[str]:
        """Находит исходную модель для переменной через BFS по графу."""
        visited = set()
        queue = [var_name]
        
        while queue:
            current = queue.pop(0)
            if current in visited or current not in self.nodes:
                continue
            visited.add(current)
            
            node = self.nodes[current]
            
            # Если это результат model.predict() - нашли модель
            if node.method_call in ['predict', 'predict_proba', 'fit',
                                   'transform', 'score', 'decision_function']:
                if node.parent_obj:
                    return node.parent_obj
            
            # Приоритизируем зависимости: сначала те, у которых есть method_call
            deps_with_methods = []
            deps_without_methods = []
            
            for dep in node.assigned_from:
                if dep in self.nodes and self.nodes[dep].method_call:
                    deps_with_methods.append(dep)
                else:
                    deps_without_methods.append(dep)
            
            # Добавляем в очередь: сначала с методами, потом без
            queue.extend(deps_with_methods)
            queue.extend(deps_without_methods)
            
        return None


class NotebookAnalyzer(ast.NodeVisitor):
    """AST visitor для построения графа зависимостей."""
    
    def __init__(self):
        self.graph = DependencyGraph()
        self.current_deps: Set[str] = set()
        self.current_method: Optional[str] = None
        self.current_parent: Optional[str] = None
        
    def visit_Assign(self, node: ast.Assign):
        """Обрабатываем присваивание: a = expr"""
        self.current_deps = set()
        self.current_method = None
        self.current_parent = None
        
        self.visit(node.value)
        
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.graph.add_assignment(
                    target.id, 
                    self.current_deps.copy(),
                    self.current_method,
                    self.current_parent
                )
        
        self.generic_visit(node)
        
    def visit_Name(self, node: ast.Name):
        """Собираем имена переменных в Load context."""
        if isinstance(node.ctx, ast.Load):
            self.current_deps.add(node.id)
        self.generic_visit(node)
        
    def visit_Call(self, node: ast.Call):
        """Обрабатываем вызовы: obj.method(args) и func(args)"""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                self.current_parent = node.func.value.id
                self.current_method = node.func.attr
                self.current_deps.add(node.func.value.id)
        
        # Собираем зависимости из аргументов
        for arg in node.args:
            self.visit(arg)
        for kw in node.keywords:
            self.visit(kw.value)
            
    def visit_Subscript(self, node: ast.Subscript):
        """Обрабатываем срезы: y_prob[:, 1] - сохраняем зависимость"""
        self.visit(node.value)
        self.generic_visit(node)


class PlotCallAnalyzer(ast.NodeVisitor):
    """Анализирует вызовы matplotlib для привязки графиков к переменным."""
    
    def __init__(self):
        self.plot_calls: List[Dict[str, Any]] = []
        self.current_call_args: Set[str] = set()
        
    def visit_Call(self, node: ast.Call):
        """Ищем вызовы plt.plot, plt.hist, plt.scatter и т.д."""
        is_plot_call = False
        
        # plt.hist(...) или matplotlib.pyplot.hist(...)
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in ['plt', 'pyplot']:
                    if node.func.attr in ['plot', 'scatter', 'hist', 'bar', 
                                         'imshow', 'contour', 'boxplot', 'violin',
                                         'pie', 'fill', 'step']:
                        is_plot_call = True
                        
        if is_plot_call:
            # Собираем переменные из аргументов
            self.current_call_args = set()
            for arg in node.args:
                self._collect_names(arg)
            for kw in node.keywords:
                self._collect_names(kw.value)
                
            self.plot_calls.append({
                "function": node.func.attr if isinstance(node.func, ast.Attribute) else "unknown",
                "variables": self.current_call_args.copy()
            })
            
        self.generic_visit(node)
        
    def _collect_names(self, node):
        """Рекурсивно собирает имена переменных из выражения."""
        if isinstance(node, ast.Name):
            self.current_call_args.add(node.id)
        elif isinstance(node, ast.Subscript):
            # y_prob[:, 1] -> y_prob
            self._collect_names(node.value)
        elif isinstance(node, ast.Attribute):
            # obj.attr -> obj
            self._collect_names(node.value)
        elif isinstance(node, (ast.BinOp, ast.UnaryOp)):
            for child in ast.iter_child_nodes(node):
                self._collect_names(child)


def extract_plot_variable_mapping(code: str, graph: DependencyGraph) -> Dict[int, Optional[str]]:
    """
    Анализирует вызовы plt.* и возвращает mapping:
    {plot_index: model_var_name}
    
    plot_index = порядковый номер вызова plt.* в коде (1-based)
    """
    try:
        # Очищаем код от магий
        cleaned_lines = []
        for line in code.split("\n"):
            if line.strip().startswith(("%%", "%")) or "get_ipython()" in line:
                cleaned_lines.append("")
            else:
                cleaned_lines.append(line)
        clean_code = "\n".join(cleaned_lines)
        
        tree = ast.parse(clean_code)
        analyzer = PlotCallAnalyzer()
        analyzer.visit(tree)
        
        mapping = {}
        for idx, call_info in enumerate(analyzer.plot_calls, start=1):
            # Находим модель для любой переменной из вызова
            model_found = None
            for var in call_info["variables"]:
                origin = graph.get_origin_model(var)
                if origin:
                    model_found = origin
                    break
            mapping[idx] = model_found
            
        return mapping
        
    except SyntaxError:
        return {}


def build_lineage_from_code(code: str) -> DependencyGraph:
    """Строит граф зависимостей из кода."""
    # Очищаем от IPython магий
    cleaned_lines = []
    for line in code.split("\n"):
        stripped = line.strip()
        if stripped.startswith(("%%", "%")) or "get_ipython()" in stripped:
            cleaned_lines.append("")  # Пустая строка сохраняет номера
        else:
            cleaned_lines.append(line)
    
    clean_code = "\n".join(cleaned_lines)
    
    try:
        tree = ast.parse(clean_code)
        analyzer = NotebookAnalyzer()
        analyzer.visit(tree)
        return analyzer.graph
    except SyntaxError as e:
        print(f"Warning: AST parsing failed: {e}")
        return DependencyGraph()


def classify_variables(namespace: Dict[str, Any], graph: DependencyGraph) -> Dict[str, str]:
    """
    Классифицирует переменные в namespace.
    Возвращает mapping: {var_name: model_var_name or "ungrouped"}
    """
    import inspect
    
    models = {k: v for k, v in namespace.items() 
              if hasattr(v, "predict") 
              and not inspect.isclass(v) 
              and not k.startswith("_")}
    
    mapping: Dict[str, str] = {}
    
    for var_name in namespace.keys():
        if var_name.startswith("_"):
            continue
            
        if var_name in models:
            mapping[var_name] = var_name
            continue
            
        origin = graph.get_origin_model(var_name)
        if origin and origin in models:
            mapping[var_name] = origin
        else:
            mapping[var_name] = "ungrouped"
            
    return mapping
