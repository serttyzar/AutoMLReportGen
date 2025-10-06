# cli.py
import typer
from pathlib import Path
from .io.json_source import load_experiment_set
from .rendering.renderer import render_html, render_report_with_bundle
app = typer.Typer(add_completion=False)

@app.command()
def init():
    base = Path("templates") / "custom"
    base.mkdir(parents=True, exist_ok=True)
    (base / "default.html.j2").write_text("<!-- override me -->", encoding="utf-8")
    typer.echo("Initialized templates/custom")

@app.command()
def demo(outdir: str = "reports"):
    import numpy as np
    import matplotlib.pyplot as plt
    from sklearn.datasets import make_classification
    from sklearn.linear_model import LogisticRegression

    from autoreport.capture.runtime import RuntimeCapture
    from autoreport.tracker import run_experiment
    from autoreport.io.json_source import save_run

    X, y = make_classification(n_samples=500, n_features=8, random_state=42)
    clf = LogisticRegression(max_iter=200, random_state=42)
    with RuntimeCapture() as rc:
        clf.fit(X, y)
        y_pred = clf.predict(X)
        y_prob = clf.predict_proba(X)[:, 1]
        plt.figure()
        plt.hist(y_prob, bins=20, color="#4C78A8", alpha=0.85)
        plt.title("Score distribution (demo)")
        plt.xlabel("p(class=1)")
        plt.ylabel("count")

    ns = {"y_true_main": y, "y_pred_main": y_pred, "y_prob_main": y_prob}
    run = run_experiment(
        code="# demo",
        namespace=ns,
        run_name="demo_run",
        stdout=rc.stdout,
        stderr=rc.stderr,
        error=rc.error,
        duration_s=rc.duration_s,
    )
    export_dir = Path("export")
    save_run(run, export_dir)

    template_dir = Path(__file__).resolve().parent / "rendering" / "templates"
    report_dir = Path(outdir) / run.id
    result = render_report_with_bundle(
        template_dir, "default.html.j2",
        {"run": run.model_dump()},
        report_dir=report_dir,
        bundle_mode="copy"
    )
    typer.echo(f"Demo report: {result}")

@app.command()
def generate(export_dir: str = "export", outdir: str = "reports", template: str = "default.html.j2"):
    es = load_experiment_set(Path(export_dir))
    if not es.runs:
        raise typer.Exit(code=1)
    run = es.runs[-1]
    template_dir = Path(__file__).resolve().parent / "rendering" / "templates"
    report_dir = Path(outdir) / run.id
    result = render_report_with_bundle(
        template_dir, template,
        {"run": run.model_dump()},
        report_dir=report_dir,
        bundle_mode="copy"
    )
    typer.echo(f"Generated: {result}")

def run():
    app()

if __name__ == "__main__":
    run()
