"""Build a bank-statement style PDF with ReportLab."""

from datetime import datetime
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

NAVY = colors.HexColor("#14213D")
ROYAL = colors.HexColor("#2563EB")
MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#E2E8F0")
CANVAS = colors.HexColor("#F8FAFC")
INK = colors.HexColor("#1E293B")
CREDIT = colors.HexColor("#16A34A")
DEBIT = colors.HexColor("#DC2626")

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 18 * mm
CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN)


def format_inr(value):
    """Indian digit grouping: 12,34,567.89"""
    amount = Decimal(str(value)).quantize(Decimal("0.01"))
    negative = amount < 0
    whole, decimals = f"{abs(amount):.2f}".split(".")

    if len(whole) > 3:
        last_three = whole[-3:]
        rest = whole[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        whole = ",".join(groups + [last_three])

    return f"{'-' if negative else ''}Rs. {whole}.{decimals}"


def pretty_date(iso_date):
    try:
        return datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d %b %Y")
    except (TypeError, ValueError):
        return iso_date or "-"


def _styles():
    return {
        "brand": ParagraphStyle(
            "brand",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=colors.white,
        ),
        "brand_sub": ParagraphStyle(
            "brand_sub",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#CBD5E1"),
        ),
        "h1": ParagraphStyle(
            "h1", fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=NAVY
        ),
        "muted": ParagraphStyle(
            "muted", fontName="Helvetica", fontSize=8.5, leading=12, textColor=MUTED
        ),
        "label": ParagraphStyle(
            "label", fontName="Helvetica", fontSize=8, leading=11, textColor=MUTED
        ),
        "value": ParagraphStyle(
            "value", fontName="Helvetica-Bold", fontSize=9.5, leading=12.5, textColor=INK
        ),
        "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8, leading=10.5, textColor=INK),
        "cell_bold": ParagraphStyle(
            "cell_bold", fontName="Helvetica-Bold", fontSize=8, leading=10.5, textColor=INK
        ),
        "summary_label": ParagraphStyle(
            "summary_label", fontName="Helvetica", fontSize=7.5, leading=10, textColor=MUTED
        ),
        "summary_value": ParagraphStyle(
            "summary_value", fontName="Helvetica-Bold", fontSize=10.5, leading=13, textColor=NAVY
        ),
        "summary_value_light": ParagraphStyle(
            "summary_value_light",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.white,
        ),
        "summary_label_light": ParagraphStyle(
            "summary_label_light",
            fontName="Helvetica",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#CBD5E1"),
        ),
    }


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 16 * mm, PAGE_WIDTH - MARGIN, 16 * mm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        MARGIN,
        11.5 * mm,
        "Account Statement Generator  |  Educational prototype  |  All figures are dummy data",
    )
    canvas.drawRightString(PAGE_WIDTH - MARGIN, 11.5 * mm, f"Page {canvas.getPageNumber()}")
    canvas.restoreState()


def _header_block(styles):
    brand = Paragraph(
        'Account Statement Generator<br/>'
        '<font size="7.5" color="#93C5FD">STATEMENT OF ACCOUNT</font>',
        styles["brand"],
    )
    generated = Paragraph(
        f"Generated on<br/><b>{datetime.now().strftime('%d %b %Y, %I:%M %p')}</b>",
        ParagraphStyle(
            "gen", fontName="Helvetica", fontSize=8, leading=12, alignment=2,
            textColor=colors.HexColor("#CBD5E1"),
        ),
    )
    table = Table([[brand, generated]], colWidths=[CONTENT_WIDTH * 0.65, CONTENT_WIDTH * 0.35])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 12),
                ("RIGHTPADDING", (-1, 0), (-1, 0), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def _account_block(statement, styles):
    account = statement["account"]
    period = statement["period"]

    left = [
        [Paragraph("ACCOUNT HOLDER", styles["label"]), Paragraph("ACCOUNT NUMBER", styles["label"])],
        [
            Paragraph(account["account_holder"], styles["value"]),
            Paragraph(f"XXXX {account['account_number_masked'][-4:]}", styles["value"]),
        ],
        [Paragraph("ACCOUNT TYPE", styles["label"]), Paragraph("STATEMENT PERIOD", styles["label"])],
        [
            Paragraph(account["account_type"], styles["value"]),
            Paragraph(
                f"{pretty_date(period['start_date'])} - {pretty_date(period['end_date'])}",
                styles["value"],
            ),
        ],
    ]

    table = Table(left, colWidths=[CONTENT_WIDTH * 0.5, CONTENT_WIDTH * 0.5])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CANVAS),
                ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.white),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return table


def _summary_block(statement, styles):
    cells = [
        ("OPENING BALANCE", format_inr(statement["opening_balance"]), False),
        ("TOTAL CREDITS", f"+ {format_inr(statement['total_credits'])}", False),
        ("TOTAL DEBITS", f"- {format_inr(statement['total_debits'])}", False),
        ("CLOSING BALANCE", format_inr(statement["closing_balance"]), True),
    ]

    header_row = [
        Paragraph(label, styles["summary_label_light"] if highlight else styles["summary_label"])
        for label, _, highlight in cells
    ]
    value_row = [
        Paragraph(value, styles["summary_value_light"] if highlight else styles["summary_value"])
        for _, value, highlight in cells
    ]

    table = Table([header_row, value_row], colWidths=[CONTENT_WIDTH / 4] * 4)
    style = [
        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    for index, (_, _, highlight) in enumerate(cells):
        if highlight:
            style.append(("BACKGROUND", (index, 0), (index, -1), NAVY))
    table.setStyle(TableStyle(style))
    return table


def _transactions_block(statement, styles):
    header = ["Date", "Description", "Transaction ID", "Debit", "Credit", "Balance"]
    rows = [
        [Paragraph(f"<b>{label}</b>", styles["cell_bold"]) for label in header]
    ]
    alignments = [
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
    ]
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), ROYAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 1), (-1, -1), 0.4, BORDER),
    ]

    for row_index, line in enumerate(statement["transactions"], start=1):
        rows.append(
            [
                Paragraph(pretty_date(line["transaction_date"]), styles["cell"]),
                Paragraph(line["description"], styles["cell"]),
                Paragraph(line["reference"], styles["cell"]),
                Paragraph(format_inr(line["debit"]) if line["debit"] != "0.00" else "-", styles["cell"]),
                Paragraph(format_inr(line["credit"]) if line["credit"] != "0.00" else "-", styles["cell"]),
                Paragraph(f"<b>{format_inr(line['balance'])}</b>", styles["cell"]),
            ]
        )
        style.append(("TEXTCOLOR", (4, row_index), (4, row_index), CREDIT))
        style.append(("TEXTCOLOR", (3, row_index), (3, row_index), DEBIT))
        if row_index % 2 == 0:
            style.append(("BACKGROUND", (0, row_index), (-1, row_index), colors.HexColor("#F8FAFC")))

    if not statement["transactions"]:
        rows.append(
            [
                Paragraph("No transactions in this period.", styles["cell"]),
                "",
                "",
                "",
                "",
                "",
            ]
        )
        style.append(("SPAN", (0, 1), (-1, 1)))
        style.append(("ALIGN", (0, 1), (-1, 1), "CENTER"))
        style.append(("TOPPADDING", (0, 1), (-1, 1), 14))
        style.append(("BOTTOMPADDING", (0, 1), (-1, 1), 14))

    width = CONTENT_WIDTH
    col_widths = [width * 0.14, width * 0.33, width * 0.16, width * 0.12, width * 0.12, width * 0.13]

    if statement["transactions"]:
        rows.append(
            [
                "",
                Paragraph("<b>Total for the period</b>", styles["cell_bold"]),
                Paragraph(
                    f"{statement['transaction_count']} transaction(s)", styles["cell"]
                ),
                Paragraph(f"<b>{format_inr(statement['total_debits'])}</b>", styles["cell"]),
                Paragraph(f"<b>{format_inr(statement['total_credits'])}</b>", styles["cell"]),
                Paragraph(f"<b>{format_inr(statement['closing_balance'])}</b>", styles["cell"]),
            ]
        )
        last = len(rows) - 1
        style.append(("BACKGROUND", (0, last), (-1, last), CANVAS))
        style.append(("SPAN", (0, last), (0, last)))
        style.append(("LINEABOVE", (0, last), (-1, last), 0.7, NAVY))

    table = Table(rows, colWidths=col_widths, repeatRows=1)
    style.extend(alignments)
    table.setStyle(TableStyle(style))
    return table


def generate_statement_pdf(statement):
    """Return a BytesIO containing the ready-to-download PDF."""
    buffer = BytesIO()
    styles = _styles()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=16 * mm,
        bottomMargin=22 * mm,
        title="Account Statement",
        author="Account Statement Generator",
    )

    story = [
        _header_block(styles),
        Spacer(1, 8 * mm),
        Paragraph("Account Statement", styles["h1"]),
        Spacer(1, 1.5 * mm),
        Paragraph(
            f"Statement for the period {pretty_date(statement['period']['start_date'])} to "
            f"{pretty_date(statement['period']['end_date'])}",
            styles["muted"],
        ),
        Spacer(1, 5 * mm),
        _account_block(statement, styles),
        Spacer(1, 4 * mm),
        _summary_block(statement, styles),
        Spacer(1, 6 * mm),
        Paragraph("Transaction details", styles["cell_bold"]),
        Spacer(1, 2.5 * mm),
        _transactions_block(statement, styles),
        Spacer(1, 6 * mm),
        Paragraph(
            "This statement is a computer generated document produced by an educational "
            "prototype. It does not represent an actual bank account and must not be used "
            "for financial, legal or tax purposes.",
            styles["muted"],
        ),
    ]

    document.build(story, onFirstPage=_footer, onLaterPages=_footer)
    buffer.seek(0)
    return buffer
