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
