from jinja2 import Environment, FileSystemLoader
from markdown_pdf import MarkdownPdf, Section
import os

def generate_report(run_info, comparison, analysis):
    env = Environment(loader=FileSystemLoader("reportgen/templates"))
    template = env.get_template("report_template.md.j2")

    output_md = template.render(run=run_info, comparison=comparison, analysis=analysis)
    output_path_md = f"outputs/reports/report_{run_info['run_id']}.md"
    output_path_pdf = output_path_md.replace(".md", ".pdf")

    os.makedirs("outputs/reports", exist_ok=True)
    with open(output_path_md, "w", encoding="utf-8") as f:
        f.write(output_md)

    with open(output_path_md, "r", encoding="utf-8") as f:
        md_content = f.read()

    pdf = MarkdownPdf(toc_level=2, optimize=True)
    pdf.add_section(Section(md_content))
    pdf.save(output_path_pdf)

    print(f"Отчет сохранен: {output_path_pdf}")
