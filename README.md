# AutoMLReportGen

Программная система автоматической генерации отчетов по экспериментам машинного обучения. Система предназначена для пользователей, работающих с Jupyter Notebook, которым требуется автоматическое формирование отчета о ходе экспериментов машинного обучения.

## Описание

AutoMLReportGen представляет собой инструмент для автоматизированного создания отчетов с полным перечнем моделей, графиков и метрик, группированных между собой. Система позволяет формировать единый интерактивный отчет по всему ноутбуку без ручного сбора информации.

Основная особенность системы заключается в том, что для создания отчета достаточно вставить одну команду `%%autoreport` в последнюю ячейку среды Jupyter Notebook, добавить после нее комментарий (например, `# full notebook`) и выполнить ячейку. Система автоматически соберет весь код, результаты и метаданные и сформирует итоговый HTML-отчет, который структурирует проделанную работу.

## Установка

### Клонирование репозитория

```bash
git clone https://github.com/serttyzar/AutoMLReportGen
```

### Переход в директорию проекта

```bash
cd AutoMLReportGen
```

### Установка пакета

```bash
pip install -e .
```

### Системные требования

- Python >= 3.10
- Зависимости (устанавливаются автоматически):
  - pydantic >= 2.3
  - jinja2 >= 3.1
  - typer >= 0.12
  - matplotlib >= 3.7
  - seaborn >= 0.13
  - scikit-learn >= 1.3

## Использование

### Загрузка расширения

В начале работы с ноутбуком необходимо загрузить IPython-расширение:

```python
%load_ext autoreport
```

### Базовое использование

Для генерации отчета по всему ноутбуку добавьте в последнюю ячейку:

```python
%%autoreport
# full notebook
```

После выполнения ячейки система создаст HTML-отчет в директории `reports/<run_id>/index.html`.

### Параметры команды

Команда `%%autoreport` поддерживает следующие параметры:

- `--name` — название эксперимента (по умолчанию: "SmartRun")
- `--template` — имя шаблона для отчета (по умолчанию: "default.html.j2")
- `--outdir` — директория для сохранения отчетов (по умолчанию: "reports")
- `--label` — метка для группировки результатов (по умолчанию: "main")

Пример использования с параметрами:

```python
%%autoreport --name "Experiment_01" --outdir "my_reports"
# full notebook
```

### Пример полного рабочего процесса

```python
# Ячейка 1: Загрузка расширения
%load_ext autoreport

# Ячейка 2: Импорт библиотек
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
import matplotlib.pyplot as plt

# Ячейка 3: Подготовка данных
X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Ячейка 4: Обучение модели
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Ячейка 5: Оценка модели
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred, average='weighted')

# Ячейка 6: Визуализация
plt.figure(figsize=(8, 6))
plt.scatter(X_test[:, 0], X_test[:, 1], c=y_pred, cmap='viridis')
plt.title('Model Predictions')
plt.xlabel('Feature 1')
plt.ylabel('Feature 2')
plt.show()

# Ячейка 7: Генерация отчета
%%autoreport --name "Iris_Classification"
# full notebook
```

### Программный интерфейс (Session API)

Для более гибкого управления процессом создания отчета доступен Session API:

```python
from autoreport.session import get_session

# Создание сессии
session = get_session(name="MyExperiment")

# Выполнение эксперимента
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# Логирование предсказаний
session.log_predictions(y_test, y_pred, label="test")

# Логирование параметров
session.log_params({"n_estimators": 100, "random_state": 42})

# Финализация и создание отчета
run = session.finalize(code="# experiment code", duration_s=1.5)
```

## Архитектура системы

### Структура проекта

```
autoreport/
├── __init__.py              # Точка входа для IPython extension
├── magics.py                # Реализация IPython magic-команд
├── session.py               # Session API для программного использования
├── tracker.py               # Логика отслеживания экспериментов
├── capture/                 # Модули захвата данных
│   ├── __init__.py
│   ├── figures.py           # Захват matplotlib/seaborn графиков
│   ├── lineage.py           # AST-анализ зависимостей переменных
│   ├── runtime.py           # Захват stdout/stderr и времени выполнения
│   └── variables.py         # Анализ переменных в namespace
├── core/                    # Базовые модели данных
│   ├── __init__.py
│   ├── models.py            # Pydantic-модели (Run, Metric, Artifact)
│   └── utils.py             # Вспомогательные функции
├── io/                      # Модули ввода/вывода
│   ├── __init__.py
│   ├── bundle.py            # Сборка артефактов в отчет
│   └── json_source.py       # Сохранение/загрузка данных в JSON
└── rendering/               # Модули генерации отчетов
    ├── __init__.py
    ├── renderer.py          # Рендеринг HTML через Jinja2
    └── templates/           # Шаблоны отчетов
        └── default.html.j2
```

### Принцип работы

1. **Захват кода** — система сохраняет весь выполненный код из ячеек Jupyter Notebook
2. **AST-анализ** — построение графа зависимостей между переменными для определения связей
3. **Обнаружение моделей** — автоматическое определение объектов с методом `predict()`
4. **Захват метрик** — сохранение всех числовых переменных и словарей с числовыми значениями
5. **Захват графиков** — автоматическое сохранение всех созданных matplotlib/seaborn визуализаций
6. **Группировка данных** — привязка метрик и графиков к соответствующим моделям
7. **Генерация отчета** — создание HTML-файла с полной структурированной информацией

### Формат выходных данных

Система сохраняет данные о запуске в следующем формате:

```json
{
  "id": "abc123def4",
  "name": "MyExperiment",
  "duration_s": 2.5,
  "params": {
    "n_estimators": 100,
    "random_state": 42
  },
  "metrics": {
    "accuracy": {
      "name": "accuracy",
      "value": 0.95,
      "direction": "max"
    },
    "f1_score": {
      "name": "f1_score",
      "value": 0.94,
      "direction": "max"
    }
  },
  "artifacts": [
    {
      "name": "figure_1",
      "path": "assets/figure_1.png",
      "kind": "figure",
      "meta": {
        "model": "model"
      }
    }
  ],
  "code": "# full experiment code",
  "stdout": "",
  "stderr": "",
  "error": null,
  "meta": {
    "models": {
      "model": {
        "type": "RandomForestClassifier",
        "params": {
          "n_estimators": 100,
          "random_state": 42
        }
      }
    },
    "grouped_metrics": {
      "model": [
        {
          "key": "accuracy",
          "name": "accuracy",
          "value": 0.95
        }
      ]
    },
    "lineage_graph": {}
  }
}
```

## Расширение функциональности

### Создание пользовательских шаблонов

Для создания собственного шаблона отчета:

1. Создайте новый файл в директории `autoreport/rendering/templates/`
2. Используйте синтаксис Jinja2 для определения структуры отчета
3. Укажите имя шаблона в параметре `--template`

Доступные переменные в шаблоне:
- `run` — объект Run с полной информацией о запуске
- `now` — текущая дата и время

Пример базового шаблона:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ run.name }}</title>
</head>
<body>
    <h1>{{ run.name }}</h1>
    <p>Execution time: {{ run.duration_s }} seconds</p>
    
    <h2>Metrics</h2>
    <table>
        <tr>
            <th>Name</th>
            <th>Value</th>
        </tr>
        {% for key, metric in run.metrics.items() %}
        <tr>
            <td>{{ metric.name }}</td>
            <td>{{ metric.value|fmt }}</td>
        </tr>
        {% endfor %}
    </table>
    
    <h2>Visualizations</h2>
    {% for art in run.artifacts %}
        {% if art.kind == "figure" %}
            <div>
                <h3>{{ art.name }}</h3>
                <img src="{{ art.path }}" alt="{{ art.name }}">
            </div>
        {% endif %}
    {% endfor %}
</body>
</html>
```

### Автоматический захват метрик

Система автоматически захватывает следующие типы данных как метрики:

1. Числовые переменные (int, float):
```python
accuracy = 0.95
precision = 0.93
```

2. Словари с числовыми значениями:
```python
scores = {
    "train": 0.98,
    "test": 0.95,
    "validation": 0.96
}
```

Все захваченные метрики автоматически группируются по моделям на основе AST-анализа зависимостей.

## Тестирование

Проект включает набор тестов для проверки корректности работы:

```bash
# Запуск всех тестов
pytest tests/

# Запуск конкретного модуля тестов
pytest tests/test_tracker.py

# Запуск с подробным выводом
pytest tests/ -v
```

## Ограничения и известные проблемы

- Система работает только в среде Jupyter Notebook
- Поддерживаются только matplotlib и seaborn для автоматического захвата графиков
- AST-анализ может не распознать сложные динамические зависимости
- Требуется явное выполнение ячейки с `%%autoreport` для генерации отчета

## Лицензия

MIT License

## Контрибьюция

Для сообщения об ошибках и предложений по улучшению используйте систему issues в репозитории проекта.