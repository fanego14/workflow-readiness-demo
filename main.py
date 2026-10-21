import io
import os
from html import escape
from typing import Any, Dict

from fastapi import Body, FastAPI, Header, HTTPException, Response
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

app = FastAPI(title="Workflow Readiness Demo API")
DEMO_API_KEY = os.getenv("DEMO_API_KEY")

W, H = letter
left_margin = 0.5 * inch
right_margin = 0.5 * inch
top_margin = 0.65 * inch
bottom_margin = 0.55 * inch
content_width = W - inch

NAVY = HexColor("#1A2D4A")
GOLD = HexColor("#B7860B")
TEAL = HexColor("#0E6655")
WHITE = HexColor("#FFFFFF")
LGRAY = HexColor("#F2F3F4")
DARK = HexColor("#0E1E33")
MID = HexColor("#162236")
DMID = HexColor("#1F3A5A")
DGRAY = HexColor("#AAB4BF")
STATUS_COLORS = {
    "Ready": HexColor("#1E6B35"),
    "Needs attention": HexColor("#B7860B"),
    "Not assessed": HexColor("#536579"),
}
ALLOWED_STATUSES = set(STATUS_COLORS)
SECTIONS = (
    ("process_ownership", "Process ownership"),
    ("data_preparation", "Data preparation"),
    ("system_access", "System access"),
    ("training_readiness", "Training readiness"),
)

styles = {
    "cover_label": ParagraphStyle(
        "cover_label", fontName="Helvetica-Bold", fontSize=8, leading=10,
        textColor=GOLD, alignment=TA_CENTER,
    ),
    "cover_title": ParagraphStyle(
        "cover_title", fontName="Helvetica-Bold", fontSize=30, leading=34,
        textColor=WHITE, alignment=TA_CENTER,
    ),
    "cover_subheadline": ParagraphStyle(
        "cover_subheadline", fontName="Helvetica", fontSize=11, leading=14,
        textColor=LGRAY, alignment=TA_CENTER,
    ),
    "cover_meta": ParagraphStyle(
        "cover_meta", fontName="Helvetica", fontSize=8, leading=10,
        textColor=DGRAY, alignment=TA_CENTER,
    ),
    "body": ParagraphStyle(
        "body", fontName="Helvetica", fontSize=10, leading=15,
        textColor=LGRAY, alignment=TA_LEFT,
    ),
    "small_body": ParagraphStyle(
        "small_body", fontName="Helvetica", fontSize=8.5, leading=13,
        textColor=LGRAY, alignment=TA_LEFT,
    ),
    "box_header": ParagraphStyle(
        "box_header", fontName="Helvetica-Bold", fontSize=8, leading=10,
        textColor=GOLD, alignment=TA_LEFT,
    ),
    "section_bar": ParagraphStyle(
        "section_bar", fontName="Helvetica-Bold", fontSize=8, leading=10,
        textColor=GOLD, alignment=TA_LEFT,
    ),
    "section_name": ParagraphStyle(
        "section_name", fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=WHITE, alignment=TA_LEFT,
    ),
    "section_body": ParagraphStyle(
        "section_body", fontName="Helvetica", fontSize=9.5, leading=14,
        textColor=LGRAY, alignment=TA_LEFT,
    ),
    "disclaimer": ParagraphStyle(
        "disclaimer", fontName="Helvetica", fontSize=7.5, leading=11,
        textColor=DGRAY, alignment=TA_CENTER,
    ),
}


def clean(value: Any, fallback: str = "Not provided") -> str:
    """Return a trimmed string suitable for report text."""
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def safe_filename(value: str) -> str:
    """Create a filename-friendly string."""
    text = clean(value, "workflow-readiness-demo").lower()
    allowed = []
    for char in text:
        if char.isalnum():
            allowed.append(char)
        elif char in (" ", "-", "_"):
            allowed.append("-")
    filename = "".join(allowed)
    filename = "-".join(part for part in filename.split("-") if part)
    return filename or "workflow-readiness-demo"


def ptext(value: Any, fallback: str = "Not provided") -> str:
    """Escape text for ReportLab Paragraph markup."""
    return escape(clean(value, fallback))


def normalize_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    """Apply neutral defaults without deriving any status or summary."""
    normalized = {
        "business": clean(data.get("business"), "Not provided"),
        "contact": clean(data.get("contact"), "Not provided"),
        "email": clean(data.get("email"), "Not provided"),
        "report_date": clean(data.get("report_date"), "Not provided"),
        "sections": {},
    }
    supplied_sections = data.get("sections")
    if not isinstance(supplied_sections, dict):
        supplied_sections = {}

    for key, _label in SECTIONS:
        section = supplied_sections.get(key, {})
        if not isinstance(section, dict):
            section = {}
        status = clean(section.get("status"), "Not assessed")
        if status not in ALLOWED_STATUSES:
            raise ValueError(f"Unsupported status for {key}")
        normalized["sections"][key] = {
            "status": status,
            "explanation": clean(section.get("explanation"), "No explanation supplied."),
        }
    return normalized


def on_all_pages(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, H - 8, W, 8, fill=1, stroke=0)
    canvas.setFillColor(DARK)
    canvas.rect(0, 0, W, 36, fill=1, stroke=0)
    canvas.setFillColor(DGRAY)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(0.5 * inch, 13, "Workflow Readiness Demo")
    canvas.drawRightString(W - 0.5 * inch, 13, "Demonstration — synthetic data.")
    canvas.restoreState()


def hr_gold():
    return HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=8, spaceBefore=8)


def section_bar(text: str):
    return Table(
        [[Paragraph(ptext(text), styles["section_bar"])]],
        colWidths=[content_width],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), DARK),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]),
    )


def tinted_box(content_paragraphs, left_accent_color=GOLD, bg=DARK):
    inner = Table(
        [[paragraph] for paragraph in content_paragraphs],
        colWidths=[content_width - 28],
        style=TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]),
    )
    return Table(
        [[inner]],
        colWidths=[content_width],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("LEFTPADDING", (0, 0), (-1, -1), 14),
            ("RIGHTPADDING", (0, 0), (-1, -1), 14),
            ("TOPPADDING", (0, 0), (-1, -1), 14),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
            ("LINEAFTER", (0, 0), (0, -1), 3, left_accent_color),
        ]),
    )


def status_badge(status: str, width=112, height=24):
    label = escape(status)
    badge_style = ParagraphStyle(
        name=f"status_{safe_filename(status)}",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=WHITE,
        alignment=TA_CENTER,
    )
    return Table(
        [[Paragraph(label, badge_style)]],
        colWidths=[width],
        rowHeights=[height],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), STATUS_COLORS[status]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]),
    )


def section_row(number: str, name: str, status: str, explanation: str):
    number_style = ParagraphStyle(
        "section_number", fontName="Helvetica-Bold", fontSize=22, leading=26,
        textColor=GOLD, alignment=TA_LEFT,
    )
    header = Table(
        [[Paragraph(ptext(name), styles["section_name"]), status_badge(status)]],
        colWidths=[content_width - 48 - 122, 112],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]),
    )
    content = Table(
        [[header], [Paragraph(ptext(explanation), styles["section_body"])]],
        colWidths=[content_width - 48],
        style=TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]),
    )
    row = Table(
        [[Paragraph(number, number_style), content]],
        colWidths=[48, content_width - 48],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, DMID),
        ]),
    )
    return KeepTogether([row])


def build_pdf(data: Dict[str, Any]) -> bytes:
    safe_data = normalize_payload(data)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=top_margin,
        bottomMargin=bottom_margin,
    )
    story = [
        Spacer(1, 52),
        Paragraph("Demonstration — synthetic data.", styles["cover_label"]),
        Spacer(1, 8),
        Paragraph("Workflow Readiness<br/>Demo", styles["cover_title"]),
        Spacer(1, 18),
        hr_gold(),
        Spacer(1, 10),
        Paragraph(
            "Fictional customer-onboarding example",
            styles["cover_subheadline"],
        ),
        Spacer(1, 8),
        Paragraph(
            f"Business: {ptext(safe_data['business'])} &nbsp;·&nbsp; "
            f"Contact: {ptext(safe_data['contact'])}",
            styles["cover_meta"],
        ),
        Paragraph(
            f"Email: {ptext(safe_data['email'])} &nbsp;·&nbsp; "
            f"Report date: {ptext(safe_data['report_date'])}",
            styles["cover_meta"],
        ),
        Spacer(1, 34),
        tinted_box([
            Paragraph("Demonstration — synthetic data.", styles["box_header"]),
            Paragraph(
                "Section statuses and explanations are supplied example content. "
                "No combined score or overall readiness judgment is calculated.",
                styles["small_body"],
            ),
        ], left_accent_color=TEAL, bg=MID),
        Spacer(1, 20),
        section_bar("ONBOARDING WORKFLOW SECTIONS"),
        Spacer(1, 4),
    ]

    for index, (key, label) in enumerate(SECTIONS, start=1):
        section = safe_data["sections"][key]
        story.append(section_row(
            f"{index:02d}", label, section["status"], section["explanation"]
        ))

    story.extend([
        Spacer(1, 18),
        hr_gold(),
        Paragraph(
            "This portfolio demonstration uses fictional sample content only.",
            styles["disclaimer"],
        ),
    ])
    doc.build(story, onFirstPage=on_all_pages, onLaterPages=on_all_pages)
    buffer.seek(0)
    return buffer.read()


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Workflow Readiness Demo",
        "endpoints": ["/health", "/generate-pdf"],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-pdf")
async def generate_pdf(
    payload: Dict[str, Any] = Body(default_factory=dict),
    x_demo_api_key: str | None = Header(default=None, alias="X-Demo-API-Key"),
):
    if not DEMO_API_KEY:
        raise HTTPException(status_code=503, detail="PDF generation is not configured")
    if x_demo_api_key != DEMO_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        pdf_bytes = build_pdf(payload)
        normalized = normalize_payload(payload)
        filename = f"workflow-readiness-{safe_filename(normalized['business'])}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid demonstration input") from None
    except Exception:
        raise HTTPException(status_code=500, detail="PDF generation failed") from None