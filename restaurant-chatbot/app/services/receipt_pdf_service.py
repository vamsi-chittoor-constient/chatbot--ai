"""
Receipt PDF Generation Service
===============================
Generates PDF receipts from payment state data using reportlab.
"""

import io
from typing import Dict, Any, List
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

import structlog

logger = structlog.get_logger("services.receipt_pdf")

# Receipt page size: 80mm thermal receipt width, variable height
RECEIPT_WIDTH = 80 * mm
RECEIPT_HEIGHT = 297 * mm  # A4 height as max


def generate_receipt_pdf(payment_state: Dict[str, Any]) -> bytes:
    """
    Generate a PDF receipt from payment state data.

    Args:
        payment_state: Payment state dict from Redis containing:
            - order_id: Display order ID (e.g. "ORD-830A98E5")
            - order_number: Invoice number
            - amount: Total amount paid
            - payment_id: Razorpay payment ID
            - method: Payment method
            - items: List of cart items [{name, price, quantity}, ...]
            - order_type: dine_in / take_away
            - completed_at: Payment completion timestamp

    Returns:
        PDF file bytes
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "ReceiptTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=2 * mm,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "ReceiptSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=4 * mm,
    )
    heading_style = ParagraphStyle(
        "ReceiptHeading",
        parent=styles["Heading3"],
        fontSize=11,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
    normal_style = ParagraphStyle(
        "ReceiptNormal",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=1 * mm,
    )
    bold_style = ParagraphStyle(
        "ReceiptBold",
        parent=styles["Normal"],
        fontSize=11,
        spaceAfter=1 * mm,
        fontName="Helvetica-Bold",
    )
    right_style = ParagraphStyle(
        "ReceiptRight",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_RIGHT,
    )
    center_style = ParagraphStyle(
        "ReceiptCenter",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.grey,
    )

    elements = []

    # ── Header ───────────────────────────────────────────────
    elements.append(Paragraph("Order Receipt", title_style))
    elements.append(Paragraph("Restaurant AI Assistant", subtitle_style))
    elements.append(Spacer(1, 2 * mm))

    # ── Order Info ───────────────────────────────────────────
    order_number = payment_state.get("order_number") or payment_state.get("order_id", "N/A")
    order_type_raw = payment_state.get("order_type", "")
    order_type = "Take Away" if "take" in order_type_raw.lower() else "Dine In" if order_type_raw else ""
    payment_id = payment_state.get("payment_id", "")
    method_raw = payment_state.get("method", "")
    method_label = {
        "online": "Online (Razorpay)",
        "cash": "Cash",
        "card_at_counter": "Card at Counter",
        "card": "Card at Counter",
    }.get(method_raw, method_raw or "Online")

    completed_at = payment_state.get("completed_at", "")
    if completed_at:
        try:
            dt = datetime.fromisoformat(completed_at)
            date_str = dt.strftime("%B %d, %Y at %I:%M %p")
        except (ValueError, TypeError):
            date_str = completed_at
    else:
        date_str = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    info_data = [
        ["Order Number:", str(order_number)],
        ["Date:", date_str],
    ]
    if order_type:
        info_data.append(["Order Type:", order_type])
    info_data.append(["Payment Method:", method_label])
    if payment_id:
        info_data.append(["Payment ID:", str(payment_id)])
    info_data.append(["Status:", "Paid"])

    info_table = Table(info_data, colWidths=[45 * mm, 115 * mm])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 4 * mm))

    # ── Line separator ───────────────────────────────────────
    sep_table = Table([["" ]], colWidths=[160 * mm])
    sep_table.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1, colors.Color(0.85, 0.85, 0.85)),
    ]))
    elements.append(sep_table)
    elements.append(Spacer(1, 2 * mm))

    # ── Items Table ──────────────────────────────────────────
    items: List[Dict[str, Any]] = payment_state.get("items", [])
    amount = float(payment_state.get("amount", 0))
    receipt_subtotal = payment_state.get("subtotal")
    receipt_packaging = payment_state.get("packaging_charges")

    if items:
        elements.append(Paragraph("Order Items", heading_style))

        # Calculate item subtotal from items
        items_subtotal = sum(
            float(item.get("price", 0)) * int(item.get("quantity", 1))
            for item in items
        )

        table_data = [["Item", "Qty", "Price", "Total"]]
        for item in items:
            name = item.get("name", "Unknown")
            qty = int(item.get("quantity", 1))
            price = float(item.get("price", 0))
            line_total = price * qty
            table_data.append([
                name,
                str(qty),
                f"Rs.{price:.2f}",
                f"Rs.{line_total:.2f}",
            ])

        # Subtotal row (item prices only)
        subtotal_val = float(receipt_subtotal) if receipt_subtotal is not None else items_subtotal
        table_data.append(["", "", "Subtotal:", f"Rs.{subtotal_val:.2f}"])

        # Packaging charges row
        packaging_val = float(receipt_packaging) if receipt_packaging is not None else 0
        if packaging_val > 0:
            table_data.append(["", "", "Packaging:", f"Rs.{packaging_val:.2f}"])

        items_table = Table(
            table_data,
            colWidths=[80 * mm, 15 * mm, 30 * mm, 35 * mm],
        )

        # Style rows - subtotal row is second-to-last (or last if no packaging)
        subtotal_row_idx = len(table_data) - (2 if packaging_val > 0 else 1)
        items_table.setStyle(TableStyle([
            # Header
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, 0), colors.Color(0.95, 0.95, 0.95)),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            # Body
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            # Alignment
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            # Grid
            ("LINEBELOW", (0, 0), (-1, 0), 1, colors.Color(0.8, 0.8, 0.8)),
            ("LINEABOVE", (0, subtotal_row_idx), (-1, subtotal_row_idx), 1, colors.Color(0.8, 0.8, 0.8)),
            # Subtotal and packaging bold
            ("FONTNAME", (2, subtotal_row_idx), (-1, -1), "Helvetica-Bold"),
        ]))
        elements.append(items_table)
    else:
        # No items available - show total only
        elements.append(Paragraph("Order Items", heading_style))
        elements.append(Paragraph("(Itemized details not available)", normal_style))

    elements.append(Spacer(1, 4 * mm))

    # ── Total ────────────────────────────────────────────────
    sep_table2 = Table([["" ]], colWidths=[160 * mm])
    sep_table2.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 1.5, colors.Color(0.3, 0.3, 0.3)),
    ]))
    elements.append(sep_table2)

    total_data = [["Total Paid:", f"Rs.{amount:.2f}"]]
    total_table = Table(total_data, colWidths=[125 * mm, 35 * mm])
    total_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 13),
        ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(total_table)

    sep_table3 = Table([["" ]], colWidths=[160 * mm])
    sep_table3.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, colors.Color(0.3, 0.3, 0.3)),
    ]))
    elements.append(sep_table3)

    # ── Footer ───────────────────────────────────────────────
    elements.append(Spacer(1, 8 * mm))
    elements.append(Paragraph("Thank you for your order!", center_style))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        center_style,
    ))

    # Build PDF
    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    logger.info(
        "receipt_pdf_generated",
        order_id=payment_state.get("order_id"),
        size_bytes=len(pdf_bytes),
    )

    return pdf_bytes
