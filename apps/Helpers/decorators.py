from django.contrib.auth.decorators import user_passes_test

def group_required(group_names):
    """Restrict view to users in any of the given groups."""
    def in_groups(u):
        if u.is_authenticated:
            return u.groups.filter(name__in=group_names).exists() or u.is_superuser
        return False
    return user_passes_test(in_groups)

# ===== Helper functions =====
#helper function to safely parse floats
# for quoting response
# safe for floats
def safe_float(value, default=0.0):
    """
    Convert value to float safely.
    Returns `default` if conversion fails or value is empty.
    """
    try:
        if value in (None, "", "“”"):  # also catch weird empty quotes
            return default
        return float(value)
    except (ValueError, TypeError):
        return 

#handles/creates pdf Quotes and sends via client email
# this handles all freight types
import os
from io import BytesIO
from datetime import datetime
from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from PIL import Image as PILImage

# --- Utility Functions ---

def _wrap_table_data(data, style):
    return [[Paragraph(str(cell), style) for cell in row] for row in data]

def _style_table(table, header_bg=colors.HexColor("#E6F2FF"),
                 header_text=colors.HexColor("#003366"), show_grid=True):
    style = [
        ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 11),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BACKGROUND", (0,0), (-1,0), header_bg),
        ("TEXTCOLOR", (0,0), (-1,0), header_text),
        ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#F0FFFF")),
    ]
    if show_grid:
        style.append(("GRID", (0,0), (-1,-1), 0.5, colors.black))
    table.setStyle(TableStyle(style))

# --- Header/Footer Wrapper ---

def make_header_footer(service_type):
    """Return a header/footer function bound with service_type."""
    def _header_footer(canvas_obj, doc):
        width, height = letter
        # Full-page background white
        canvas_obj.setFillColor(colors.white)
        canvas_obj.rect(0, 0, width, height, fill=1)

        # Header
        header_height = 60
        canvas_obj.setFillColor(colors.HexColor("#E6F2FF"))
        canvas_obj.rect(0, height-header_height, width, header_height, fill=1)

        # Logo
        logo_path = os.path.join(settings.BASE_DIR, "apps", "dependencies", "static", "img", "logo", "logo_pdf.png")
        if os.path.exists(logo_path):
            pil_logo = PILImage.open(logo_path)
            logo_width, logo_height = pil_logo.size
            max_logo_height = header_height - 15
            scale = min(1, max_logo_height/logo_height)
            canvas_obj.drawImage(logo_path, 40, height-max_logo_height-10,
                                 width=logo_width*scale, height=logo_height*scale,
                                 preserveAspectRatio=True, mask='auto')

        # Header text
        canvas_obj.setFillColor(colors.HexColor("#003366"))
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawCentredString(width/2, height-35, f"Jenik - {service_type} Quote")

        # Footer
        footer_height = 50
        canvas_obj.setFillColor(colors.HexColor("#E6F2FF"))
        canvas_obj.rect(0, 0, width, footer_height, fill=1)
        canvas_obj.setFillColor(colors.HexColor("#003366"))
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawCentredString(width/2, 20,
                                     "Jenik Freight - 3571 52nd Street SE, Level 1, Calgary, Alberta T2B 3R3, Canada")
    return _header_footer

# --- PDF Generation ---

def generate_quote_pdf(record, service_type, request_id, client_name):
    buffer = BytesIO()
    elements = []

    styles = getSampleStyleSheet()
    cell_style = styles["Normal"]
    cell_style.fontName = "Helvetica"
    cell_style.fontSize = 11
    cell_style.leading = 13

    # Info Table
    info_data = [
        ["Request ID", request_id],
        ["Client", client_name],
        ["Date Received", f"{getattr(record, 'date_received', '')} {getattr(record, 'time_received', '')}"],
        ["Quote Created", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ["Validity Date", getattr(record, "validity_date", "N/A")],
        ["Place of Receipt", getattr(record, "place_of_receipt", "N/A")],
    ]

    if service_type in ["Air Freight", "RORO Freight"]:
        info_data.extend([
            ["Number of Units", getattr(record, "number_of_units", "N/A")],
            ["Departure", f"{getattr(record, 'departure', '')}, Country: {getattr(record, 'country_of_departure', '')}"],
        ])
    if service_type == "RORO Freight":
        info_data.extend([
            ["Pick-Up Address", getattr(record, "vehicle_pickup_address", "N/A")],
            ["Delivery Address", getattr(record, "vehicle_delivery_address", "N/A")],
        ])
    elif service_type in ["Ocean Freight", "Customs Brokerage"]:
        info_data.extend([
            ["Port of Loading", f"{getattr(record, 'port_of_loading', '')}, Country: {getattr(record, 'country_of_loading', '')}"],
            ["Port of Discharge", f"{getattr(record, 'port_of_discharge', '')}, Country: {getattr(record, 'country_of_discharge', '')}"],
        ])
    if getattr(record, 'tracking', '') == "Door":
        info_data.append(["Do you require Tracking?", f"{record.tracking}, Address: {getattr(record, 'door_delivery_address', '')}"])
    else:
        info_data.append(["Do you require Tracking?", getattr(record, "tracking", "N/A")])
    
    info_data.append(["Hazardous", getattr(record, "hazardous", "N/A")])
    info_data.append(["Comments", getattr(record, "comments", "N/A")])

    info_table = Table(_wrap_table_data(info_data, cell_style), hAlign="LEFT", colWidths=[180, 320])
    _style_table(info_table, show_grid=False)
    elements.append(info_table)
    elements.append(Spacer(1, 15))

    # Package Measurements Table
    if service_type in ["Air Freight", "RORO Freight"]:
        elements.append(Paragraph("Package Measurements", ParagraphStyle('subtitle', fontSize=14, spaceAfter=10)))
        units_data = [
            [
                f"Height (<font color='red'>{getattr(record,'unit_of_measurement_L_W_H','')}</font>)",
                f"Width (<font color='red'>{getattr(record,'unit_of_measurement_L_W_H','')}</font>)",
                f"Length (<font color='red'>{getattr(record,'unit_of_measurement_L_W_H','')}</font>)",
                f"Weight (<font color='red'>{getattr(record,'unit_of_measurement_weight','')}</font>)"
            ],
            [getattr(record, "height", "N/A"), getattr(record, "width", "N/A"),
             getattr(record, "length", "N/A"), getattr(record, "weight", "N/A")]
        ]
        units_table = Table(_wrap_table_data(units_data, cell_style), hAlign="LEFT", colWidths=[120]*4)
        _style_table(units_table)
        elements.append(units_table)
        elements.append(Spacer(1, 15))

    # Commodity Type Table
    elements.append(Paragraph("Commodity Type", ParagraphStyle('subtitle', fontSize=14, spaceAfter=10)))
    commodity_data = [["Commodity Category", "Commodity Sub"]]
    commodity_data.append([getattr(record, "commodity_cat", "N/A"), getattr(record, "commodity_sub", "N/A")])
    if service_type == "Ocean Freight":
        commodity_data[0].append("Equipment Size")
        commodity_data[1].append(getattr(record, "equipment_size", "N/A"))
    commodity_table = Table(_wrap_table_data(commodity_data, cell_style), hAlign="LEFT", colWidths=[180]*len(commodity_data[0]))
    _style_table(commodity_table)
    elements.append(commodity_table)
    elements.append(Spacer(1, 15))

    # Quote Charges Table
    elements.append(Paragraph("Quote Charges", ParagraphStyle('subtitle', fontSize=14, spaceAfter=10)))
    charges = [
        ("Freight Charges", getattr(record, "freight_charges", 0)),
        ("Fuel Surcharge", getattr(record, "fuel_surcharge", 0)),
        ("Customs Charges", getattr(record, "customs_charges", 0)),
        ("Brokerage Fee", getattr(record, "brokerage_fee", 0)),
        ("Taxes", getattr(record, "taxes", 0)),
        ("Customs Duties", getattr(record, "customs_duties", 0)),
        ("Other Charges", getattr(record, "other_charges", 0)),
        ("Total Charges", getattr(record, "total_charges", 0)),
    ]
    charge_data = [["Description", f"Amount (<font color='red'>{getattr(record, 'currency_type', '')}</font>)"]]
    for label, val in charges:
        if val > 0:
            charge_data.append([label, f"{val:.2f}"])

    if len(charge_data) > 1:
        charge_table = Table(_wrap_table_data(charge_data, cell_style), hAlign="LEFT", colWidths=[250,150])

        table_style = [
            ("FONTNAME", (0,0), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,0), (-1,-1), 11),
            ("ALIGN", (0,0), (-1,-1), "LEFT"),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#E6F2FF")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.HexColor("#003366")),
            ("BACKGROUND", (0,1), (-1,-1), colors.HexColor("#F0FFFF")),
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ]

        # Highlight Total Charges row in yellow + bold text
        total_row_idx = None
        for i, row in enumerate(charge_data):
            if row[0] == "Total Charges":
                total_row_idx = i
                break
        if total_row_idx:
            table_style.append(("BACKGROUND", (0,total_row_idx), (-1,total_row_idx), colors.yellow))
            table_style.append(("FONTNAME", (0,total_row_idx), (-1,total_row_idx), "Helvetica-Bold"))

        charge_table.setStyle(TableStyle(table_style))
        elements.append(charge_table)
        elements.append(Spacer(1, 20))

    # Thank You Message
    thank_style = ParagraphStyle('thank', fontSize=16, textColor=colors.HexColor("#003366"),
                                 alignment=1, spaceBefore=20, spaceAfter=20, italic=True)
    elements.append(Paragraph("Thank you for choosing Jenik Freight!", thank_style))

    # Build PDF
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=80, bottomMargin=80)
    doc.build(elements, onFirstPage=make_header_footer(service_type), onLaterPages=make_header_footer(service_type))
    buffer.seek(0)
    return buffer

# --- Email Sending ---

def send_quote_email(record, service_type, request_id, client_name, user_email, company_email):
    pdf_buffer = generate_quote_pdf(record, service_type, request_id, client_name)
    subject = f"Jenik Freight: Your {service_type} Quote has been updated"
    recipients = [user_email, company_email]

    html_message = f"""
        <p>Dear {client_name},</p>
        <p>Your {service_type} Quote has been updated.</p>
        <p>Request ID: <b>{request_id}</b><br>CRM URL: <a href="{settings.APP_URL}">Click Here</a></p>
        <p>Thank you for choosing Jenik Freight.</p>
    """
    email = EmailMessage(subject, html_message, settings.EMAIL_HOST_USER, recipients)
    email.content_subtype = "html"
    email.attach("Quote_request.pdf",pdf_buffer.read(), "application/pdf")
    email.send()
# --- End of File ---
#------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------

