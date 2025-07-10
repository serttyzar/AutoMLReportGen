def analyze_run(run_info, comparison):
    analysis = []
    metrics = run_info["metrics"]
    params = run_info["params"]

    if not comparison or "message" in comparison:
        analysis.append("Недостаточно данных для анализа изменений, так как предыдущий эксперимент отсутствует.")
        return analysis

    for metric, values in comparison.items():
        delta = values["delta"]
        if delta > 0.01:
            analysis.append(f"Метрика {metric} улучшилась на {delta}. Возможная причина: параметры: {params}.")
        elif delta < -0.01:
            analysis.append(f"Метрика {metric} ухудшилась на {abs(delta)}. Проверь изменения гиперпараметров: {params}.")
        else:
            analysis.append(f"Метрика {metric} изменилась незначительно ({delta}).")

    if "dropout" in params:
        dp = float(params["dropout"])
        if dp > 0.4:
            analysis.append("Dropout может быть слишком высоким, возможна недообученность.")

    return analysis