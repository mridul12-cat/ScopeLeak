import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from backend.app.models.change_order import ChangeOrder
from backend.app.models.project import Project

def generate_change_order_pdf(change_order: ChangeOrder, project: Project) -> bytes:
    """Generate a clean, professional PDF for a change order."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    primary_color = colors.HexColor("#0F172A")  # Slate 900
    brand_blue = colors.HexColor("#2563EB")     # Blue 600
    muted_text = colors.HexColor("#64748B")     # Slate 500

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=primary_color,
        fontName="Helvetica-Bold",
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=muted_text,
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=primary_color,
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=6,
    )

    normal_style = ParagraphStyle(
        "NormalText",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B"),
    )

    bold_style = ParagraphStyle(
        "BoldText",
        parent=normal_style,
        fontName="Helvetica-Bold",
    )

    elements = []

    # Header block
    elements.append(Paragraph("SCOPELEAK CHANGE ORDER", title_style))
    elements.append(Paragraph(f"Document Reference: CO-{project.id[:6].upper()}-v{change_order.version}", subtitle_style))
    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=brand_blue, spaceBefore=0, spaceAfter=15))

    # Meta Info Table
    curr = change_order.currency or project.currency or "INR"
    status_label = change_order.status.replace("_", " ").title()

    meta_data = [
        [
            Paragraph("<b>Project:</b> " + project.name, normal_style),
            Paragraph("<b>Change Order #:</b> " + f"v{change_order.version}", normal_style)
        ],
        [
            Paragraph("<b>Client:</b> " + project.client_name, normal_style),
            Paragraph("<b>Date:</b> " + change_order.created_at.strftime("%B %d, %Y"), normal_style)
        ],
        [
            Paragraph("<b>Title:</b> " + change_order.title, normal_style),
            Paragraph("<b>Status:</b> " + status_label, normal_style)
        ],
        [
            Paragraph("<b>Validity:</b> " + f"{change_order.validity_days or 14} days from issuance", normal_style),
            Paragraph("<b>Payment Terms:</b> " + (change_order.payment_terms or "Standard terms"), normal_style)
        ]
    ]

    meta_table = Table(meta_data, colWidths=[3.2 * inch, 3.2 * inch])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#F1F5F9")),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 15))

    # Line Items Table
    elements.append(Paragraph("Scope Modification Line Items", section_heading))

    line_items_data = [
        [
            Paragraph("<b>Item Description</b>", bold_style),
            Paragraph("<b>Hours</b>", bold_style),
            Paragraph("<b>Rate</b>", bold_style),
            Paragraph("<b>Amount</b>", bold_style),
        ]
    ]

    items = change_order.line_items
    if not items:
        line_items_data.append([
            Paragraph("No line items specified", normal_style),
            Paragraph("-", normal_style),
            Paragraph("-", normal_style),
            Paragraph(f"{curr} 0.00", normal_style),
        ])
    else:
        for it in items:
            desc = it.get("title", "")
            if it.get("description"):
                desc += f"<br/><font color='#64748B' size='8'>{it.get('description')}</font>"
            hours = f"{it.get('hours', 0.0):.1f}"
            rate = f"{curr} {it.get('rate', 0.0):,.2f}"
            tot = f"{curr} {it.get('line_total', 0.0):,.2f}"

            line_items_data.append([
                Paragraph(desc, normal_style),
                Paragraph(hours, normal_style),
                Paragraph(rate, normal_style),
                Paragraph(tot, normal_style),
            ])

    # Totals rows
    line_items_data.append([
        Paragraph("<b>Subtotal</b>", bold_style),
        "", "",
        Paragraph(f"<b>{curr} {change_order.subtotal:,.2f}</b>", bold_style),
    ])

    if change_order.taxes > 0:
        line_items_data.append([
            Paragraph("<b>Taxes & Fees</b>", normal_style),
            "", "",
            Paragraph(f"{curr} {change_order.taxes:,.2f}", normal_style),
        ])

    line_items_data.append([
        Paragraph("<b>TOTAL AMOUNT</b>", bold_style),
        "", "",
        Paragraph(f"<b>{curr} {change_order.total:,.2f}</b>", bold_style),
    ])

    items_table = Table(line_items_data, colWidths=[3.5 * inch, 0.8 * inch, 1.1 * inch, 1.2 * inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -4 if change_order.taxes > 0 else -3), 0.5, colors.HexColor("#E2E8F0")),
        ('SPAN', (0, -3 if change_order.taxes > 0 else -2), (2, -3 if change_order.taxes > 0 else -2)),
        ('SPAN', (0, -2 if change_order.taxes > 0 else -1), (2, -2 if change_order.taxes > 0 else -1)),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#EFF6FF")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#0F172A")),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 15))

    # Terms, Assumptions & Exclusions
    if change_order.assumptions:
        elements.append(Paragraph("Assumptions", section_heading))
        elements.append(Paragraph(change_order.assumptions, normal_style))
        elements.append(Spacer(1, 8))

    if change_order.exclusions:
        elements.append(Paragraph("Exclusions", section_heading))
        elements.append(Paragraph(change_order.exclusions, normal_style))
        elements.append(Spacer(1, 8))

    # Signatures
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("Authorization & Acceptance", section_heading))
    elements.append(Paragraph(
        "By signing below, both parties confirm their agreement to these scope modifications and financial adjustments. This document amends the primary agreement.",
        normal_style
    ))
    elements.append(Spacer(1, 20))

    sig_data = [
        [
            Paragraph("<b>Submitted by (Freelancer / Agency):</b><br/><br/><br/>_____________________________________<br/>Date: ________________________", normal_style),
            Paragraph("<b>Accepted by (Client Authorized Signatory):</b><br/><br/><br/>_____________________________________<br/>Date: ________________________", normal_style),
        ]
    ]
    sig_table = Table(sig_data, colWidths=[3.2 * inch, 3.2 * inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(sig_table)

    # Footer note
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("<font size='7' color='#94A3B8'>Generated via ScopeLeak — AI Scope-Change Evidence Engine. All amounts deterministic.</font>", normal_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
