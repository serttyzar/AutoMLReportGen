from reportgen.collector import collect_latest_run
import os
import mlflow
# from reportgen.comparer import compare_with_previous
# from reportgen.analysis import analyze_run
# from reportgen.reporter import generate_report

if __name__ == "__main__":
    mlruns_path = os.path.join("examples", "content", "mlruns")
    mlflow.set_tracking_uri(f"file:{os.path.abspath(mlruns_path)}")
    experiment_name = 'MNIST Anomaly Detection - Autoencoder' 

    run_info = collect_latest_run(experiment_name)
    print(run_info)
    # comparison = compare_with_previous(run_info)
    # analysis = analyze_run(run_info, comparison)
    # generate_report(run_info, comparison, analysis)