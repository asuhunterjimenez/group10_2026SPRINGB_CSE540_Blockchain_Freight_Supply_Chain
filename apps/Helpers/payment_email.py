# payment_email.py
import os
from io import BytesIO
from decimal import Decimal
from django.conf import settings
from django.core.mail import EmailMessage
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from PIL import Image as PILImage


# ==========================================
# ETH FORMATTER
# ==========================================
def format_eth(value):
    """
    Safely format Decimal/float/string values to ETH.
    Always returns 8 decimal places.
    """
    try:
        return f"{Decimal(value):,.8f} ETH"
    except Exception:
        return "0.00000000 ETH"


# ==========================================
# PDF HEADER + FOOTER
# ==========================================
def payment_header_footer(canvas_obj, doc):
    width, height = letter

    # White page
    canvas_obj.setFillColor(colors.white)
    canvas_obj.rect(0, 0, width, height, fill=1)

    # Header
    canvas_obj.setFillColor(colors.HexColor("#E6F2FF"))
    canvas_obj.rect(0, height - 60, width, 60, fill=1)

    # Logo
    logo_path = os.path.join(
        settings.BASE_DIR,
        "static",
        "img",
        "logo",
        "logo_pdf.png"
    )

    if os.path.exists(logo_path):
        pil_logo = PILImage.open(logo_path)
        logo_width, logo_height = pil_logo.size
        scale = min(1, 40 / logo_height)

        canvas_obj.drawImage(
            logo_path,
            40,
            height - 50,
            width=logo_width * scale,
            height=logo_height * scale,
            preserveAspectRatio=True,
            mask="auto"
        )

    # Title
    canvas_obj.setFillColor(colors.HexColor("#003366"))
    canvas_obj.setFont("Helvetica-Bold", 16)
    canvas_obj.drawCentredString(
        width / 2,
        height - 35,
        "Blockchain Payment Receipt"
    )

    # Footer
    canvas_obj.setFillColor(colors.HexColor("#E6F2FF"))
    canvas_obj.rect(0, 0, width, 50, fill=1)

    canvas_obj.setFillColor(colors.HexColor("#003366"))
    canvas_obj.setFont("Helvetica", 10)
    canvas_obj.drawCentredString(
        width / 2,
        20,
        "G10 Blockchain Freight | Calgary, Alberta, Canada"
    )


# ==========================================
# GENERATE PAYMENT PDF
# ==========================================
def generate_payment_receipt_pdf(payment_record,service_type, client_name):
    buffer = BytesIO()
    elements = []
    styles = getSampleStyleSheet()

    normal_style = styles["Normal"]
    title_style = ParagraphStyle(
        "title",
        fontSize=14,
        textColor=colors.HexColor("#003366"),
        spaceAfter=10
    )

    # Receipt Title
    elements.append(Paragraph("Payment Receipt Confirmation", title_style))
    elements.append(Spacer(1, 10))

    # Payment table
    receipt_data = [
        
        ["Service Type", service_type],
        ["Client Name", client_name],
        ["Paid By User", payment_record.user],
        ["Request ID", payment_record.quote_request_id],
        ["Transaction ID", payment_record.transaction_id],
        ["Total Charges", format_eth(payment_record.total_charges)],
        ["Paid Amount", format_eth(payment_record.paid_amount)],
        ["Remaining Balance", format_eth(payment_record.balance)],
        ["Blockchain Gas Fees", format_eth(payment_record.blockchain_gas_fees)],
        [
            "Payment Date",
            payment_record.date_created.strftime("%Y-%m-%d %H:%M:%S")
            if payment_record.date_created
            else timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        ],
    ]

    table = Table(receipt_data, colWidths=[180, 320])

    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E6F2FF")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#003366")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 30))

    # Thank You
    thank_you = ParagraphStyle(
        "thank",
        fontSize=14,
        alignment=1,
        textColor=colors.HexColor("#003366")
    )
    elements.append(
        Paragraph(
            "Thank you for choosing G10 Blockchain Freight!",
            thank_you
        )
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        topMargin=80,
        bottomMargin=80,
        leftMargin=40,
        rightMargin=40
    )

    doc.build(
        elements,
        onFirstPage=payment_header_footer,
        onLaterPages=payment_header_footer
    )

    buffer.seek(0)
    return buffer


# ==========================================
# SEND PAYMENT EMAIL
# ==========================================
def send_payment_email(
    payment_record,
    service_type,
    client_name,
    user_email,
    company_email
):
    pdf_buffer = generate_payment_receipt_pdf(
        payment_record,
        service_type,
        client_name
    )

    subject = f"G10 Blockchain Freight: Payment Receipt for {service_type}"
    recipients = [user_email, company_email]

    html_message = f"""
    <p>Dear {client_name},</p>

    <p>
        We are pleased to confirm that your blockchain payment for
        <b>{service_type}</b> has been successfully received.
    </p>

    <p>
        <b>Request ID:</b> {payment_record.quote_request_id}<br>
        <b>Transaction ID:</b> {payment_record.transaction_id}<br>
        <b>Paid Amount:</b> {format_eth(payment_record.paid_amount)}
    </p>

    <p>
        Please find your <b>payment receipt confirmation attached</b>
        for your records.
    </p>

    <p>
        CRM Portal:
        <a href="{settings.APP_URL}">Click Here</a>
    </p>

    <p>
        Thank you for choosing <b>G10 Blockchain Freight</b>.
    </p>

    <p>
        Best regards,<br>
        G10 Blockchain Freight Team
    </p>
    """

    email = EmailMessage(
        subject,
        html_message,
        settings.EMAIL_HOST_USER,
        recipients
    )

    email.content_subtype = "html"
    email.attach(
        f"Payment_Receipt_{payment_record.quote_request_id}.pdf",
        pdf_buffer.read(),
        "application/pdf"
    )

    email.send()