import mlflow
import os

def collect_latest_run(experiment_name="Default"):
    client = mlflow.tracking.MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    runs = client.search_runs([experiment.experiment_id], order_by=["start_time DESC"])
    latest_run = runs[0]
    return {
        "run_id": latest_run.info.run_id,
        "params": latest_run.data.params,
        "metrics": latest_run.data.metrics,
        "tags": latest_run.data.tags,
        "start_time": latest_run.info.start_time,
    }