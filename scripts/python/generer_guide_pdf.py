#!/usr/bin/env python3
from __future__ import annotations

import textwrap
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_MD = PROJECT_ROOT / "docs" / "GUIDE_UTILISATION_OUTIL_CV.md"
OUTPUT_PDF = PROJECT_ROOT / "docs" / "GUIDE_UTILISATION_OUTIL_CV.pdf"


def draw_wrapped_line(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    font_name: str,
    font_size: float,
    max_chars: int,
    line_gap: float,
) -> float:
    c.setFont(font_name, font_size)
    chunks = textwrap.wrap(text, width=max_chars) or [""]
    for chunk in chunks:
        c.drawString(x, y, chunk)
        y -= line_gap
    return y


def render_markdown_to_pdf(source: Path, output: Path) -> None:
    lines = source.read_text(encoding="utf-8").splitlines()
    output.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output), pagesize=A4)
    page_w, page_h = A4
    margin_x = 44
    y = page_h - 48
    bottom = 46

    in_code_block = False

    def ensure_space(required: float) -> None:
        nonlocal y
        if y - required < bottom:
            c.showPage()
            y = page_h - 48

    for raw in lines:
        line = raw.rstrip()
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            ensure_space(16)
            y -= 8
            continue

        if not line.strip():
            ensure_space(14)
            y -= 10
            continue

        if in_code_block:
            ensure_space(16)
            y = draw_wrapped_line(
                c=c,
                text=line,
                x=margin_x + 10,
                y=y,
                font_name="Courier",
                font_size=9,
                max_chars=92,
                line_gap=12,
            )
            continue

        if line.startswith("# "):
            ensure_space(24)
            y = draw_wrapped_line(
                c=c,
                text=line[2:].strip(),
                x=margin_x,
                y=y,
                font_name="Helvetica-Bold",
                font_size=17,
                max_chars=62,
                line_gap=20,
            )
            y -= 4
            continue

        if line.startswith("## "):
            ensure_space(20)
            y = draw_wrapped_line(
                c=c,
                text=line[3:].strip(),
                x=margin_x,
                y=y,
                font_name="Helvetica-Bold",
                font_size=12.5,
                max_chars=85,
                line_gap=15,
            )
            y -= 2
            continue

        text = line
        if line.startswith("- "):
            text = f"- {line[2:].strip()}"

        ensure_space(15)
        y = draw_wrapped_line(
            c=c,
            text=text,
            x=margin_x,
            y=y,
            font_name="Helvetica",
            font_size=10,
            max_chars=98,
            line_gap=13,
        )

    c.save()


def main() -> None:
    if not SOURCE_MD.exists():
        raise SystemExit(f"Source markdown introuvable: {SOURCE_MD}")
    render_markdown_to_pdf(SOURCE_MD, OUTPUT_PDF)
    print(str(OUTPUT_PDF.resolve()))


if __name__ == "__main__":
    main()
