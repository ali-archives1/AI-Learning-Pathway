"""Create the reproducible biology PDF used by integration tests."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer


PAGES = (
    (
        "Foundations of Cell Biology",
        "Cell theory states that all living organisms are composed of one or more "
        "cells, the cell is the basic unit of life, and new cells arise from "
        "pre-existing cells. Prokaryotic cells lack a membrane-bound nucleus, while "
        "eukaryotic cells contain a nucleus and other membrane-bound organelles.",
    ),
    (
        "Cellular Respiration and Mitochondria",
        "Mitochondria generate most of a eukaryotic cell's ATP through cellular "
        "respiration. Their inner membrane is folded into structures called cristae. "
        "The folds increase the surface area available for the electron transport "
        "chain and ATP-producing reactions. In aerobic respiration, oxygen serves "
        "as the final electron acceptor.",
    ),
    (
        "Photosynthesis",
        "Chloroplasts capture light energy during photosynthesis. Chlorophyll in the "
        "thylakoid membranes absorbs light. The light-dependent reactions produce "
        "ATP and NADPH, and the Calvin cycle uses those products to help build sugars "
        "from carbon dioxide.",
    ),
    (
        "Genetic Information",
        "DNA stores hereditary information in a sequence of nucleotide bases. During "
        "transcription, a gene's DNA sequence is copied into RNA. Ribosomes translate "
        "messenger RNA and assemble amino acids into a polypeptide according to the "
        "genetic code.",
    ),
)


def create_test_pdf(output_path: str | Path) -> Path:
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        rightMargin=0.85 * inch,
        leftMargin=0.85 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title="Biology Study Notes",
        author="RAG Study Assistant integration fixture",
    )
    story = []
    for index, (heading, body) in enumerate(PAGES):
        story.append(Paragraph(heading, styles["Title"]))
        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph(body, styles["BodyText"]))
        story.append(Spacer(1, 0.18 * inch))
        story.append(
            Paragraph(
                f"Biology Study Notes · Page {index + 1}",
                styles["Italic"],
            )
        )
        if index < len(PAGES) - 1:
            story.append(PageBreak())
    document.build(story)
    return output


if __name__ == "__main__":
    create_test_pdf(Path(__file__).with_name("biology_test.pdf"))
