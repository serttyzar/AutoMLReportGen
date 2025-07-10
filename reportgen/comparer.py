import mlflow

def compare_with_previous(current_run_info):
    client = mlflow.tracking.MlflowClient()
    experiment_id = client.get_run(current_run_info["run_id"]).info.experiment_id
    runs = client.search_runs([experiment_id], order_by=["start_time DESC"])

    if len(runs) < 2:
        return {"message": "Нет предыдущего эксперимента", "diff": None}

    previous_run = runs[1]
    diffs = {}
    for k, v in current_run_info["metrics"].items():
        old = previous_run.data.metrics.get(k)
        if old is not None:
            delta = round(v - old, 4)
            diffs[k] = {"current": v, "previous": old, "delta": delta}
    return diffs