from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfutils
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io
from datetime import datetime
from config import Config

def register_arabic_font():
    """Register Arabic font for PDF generation"""
    try:
        # Try to register Arabic font - in production you would include font files
        # For now, we'll use default fonts with Arabic support
        pass
    except Exception as e:
        print(f"Could not register Arabic font: {e}")

def generate_invoice_pdf(sale):
    """Generate PDF invoice for a sale"""
    buffer = io.BytesIO()
    
    # Create PDF document
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Build story (content)
    story = []
    
    # Register Arabic font
    register_arabic_font()
    
    # Create styles
    styles = getSampleStyleSheet()
    
    # Custom styles for Arabic text
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Center alignment
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12,
        alignment=2,  # Right alignment for Arabic
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=2,  # Right alignment for Arabic
    )
    
    # Title
    story.append(Paragraph(Config.SHOP_NAME, title_style))
    story.append(Spacer(1, 20))
    
    # Shop information
    shop_info = f"""
    العنوان: {Config.SHOP_ADDRESS}<br/>
    الهاتف: {Config.SHOP_PHONE}<br/>
    """
    story.append(Paragraph(shop_info, header_style))
    story.append(Spacer(1, 20))
    
    # Invoice header
    invoice_header = f"""
    <b>فاتورة بيع</b><br/>
    رقم الفاتورة: {sale.invoice_no}<br/>
    التاريخ: {sale.created_at.strftime('%Y-%m-%d %H:%M')}<br/>
    الكاشير: {sale.user.name}
    """
    
    if sale.customer:
        invoice_header += f"<br/>العميل: {sale.customer.name}"
        if sale.customer.phone:
            invoice_header += f"<br/>الهاتف: {sale.customer.phone}"
    
    story.append(Paragraph(invoice_header, header_style))
    story.append(Spacer(1, 30))
    
    # Items table
    table_data = [
        ['المجموع', 'سعر الوحدة', 'الكمية', 'اسم المنتج', '#']
    ]
    
    for i, item in enumerate(sale.sale_items, 1):
        table_data.append([
            f'{item.line_total:.2f}',
            f'{item.unit_price:.2f}',
            str(item.quantity),
            item.product.name_ar,
            str(i)
        ])
    
    # Create table
    table = Table(table_data, colWidths=[1*inch, 1*inch, 0.8*inch, 2.5*inch, 0.5*inch])
    
    # Table style
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    story.append(Spacer(1, 30))
    
    # Totals
    subtotal = sum(item.line_total for item in sale.sale_items)
    
    totals_data = []
    
    if sale.discount > 0:
        totals_data.append(['', f'{subtotal:.2f}', 'المجموع الفرعي:'])
        totals_data.append(['', f'-{sale.discount:.2f}', 'الخصم:'])
    
    if sale.tax > 0:
        totals_data.append(['', f'{sale.tax:.2f}', 'الضريبة:'])
    
    totals_data.append(['', f'{sale.total:.2f}', 'المجموع الكلي:'])
    totals_data.append(['', f'{sale.paid:.2f}', 'المبلغ المدفوع:'])
    
    if sale.change > 0:
        totals_data.append(['', f'{sale.change:.2f}', 'الباقي:'])
    
    totals_table = Table(totals_data, colWidths=[1*inch, 1*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(totals_table)
    story.append(Spacer(1, 40))
    
    # Footer
    footer_text = """
    شكراً لتسوقكم معنا<br/>
    للاستفسارات يرجى الاتصال على الرقم أعلاه
    """
    story.append(Paragraph(footer_text, normal_style))
    
    # Build PDF
    doc.build(story)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

def generate_repair_receipt(repair):
    """Generate receipt for repair service"""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=2,
    )
    
    # Title
    story.append(Paragraph("إيصال استلام جهاز للصيانة", title_style))
    story.append(Paragraph(Config.SHOP_NAME, header_style))
    story.append(Spacer(1, 20))
    
    # Repair information
    repair_info = f"""
    رقم التذكرة: {repair.ticket_no}<br/>
    تاريخ الاستلام: {repair.entry_date.strftime('%Y-%m-%d %H:%M')}<br/>
    العميل: {repair.customer.name if repair.customer else 'غير محدد'}<br/>
    الهاتف: {repair.customer.phone if repair.customer and repair.customer.phone else 'غير محدد'}<br/>
    نوع الجهاز: {repair.device_model}<br/>
    المشكلة: {repair.problem_desc}<br/>
    الحالة: {repair.status}<br/>
    """
    
    if repair.parts_cost > 0:
        repair_info += f"تكلفة القطع: {repair.parts_cost:.2f}<br/>"
    
    if repair.labor_cost > 0:
        repair_info += f"أجرة العمل: {repair.labor_cost:.2f}<br/>"
    
    if repair.total_cost > 0:
        repair_info += f"التكلفة الإجمالية: {repair.total_cost:.2f}<br/>"
    
    if repair.notes:
        repair_info += f"ملاحظات: {repair.notes}<br/>"
    
    story.append(Paragraph(repair_info, header_style))
    story.append(Spacer(1, 40))
    
    # Terms and conditions
    terms = """
    الشروط والأحكام:<br/>
    - مدة الضمان على الإصلاح: شهر واحد<br/>
    - يجب إحضار هذا الإيصال عند استلام الجهاز<br/>
    - المحل غير مسؤول عن البيانات المخزنة على الجهاز<br/>
    - في حالة عدم الإصلاح خلال 30 يوم، المحل غير مسؤول عن الجهاز
    """
    story.append(Paragraph(terms, header_style))
    
    story.append(Spacer(1, 30))
    
    # Signature section
    signature_text = """
    توقيع العميل: ________________________<br/><br/>
    توقيع المستلم: ________________________
    """
    story.append(Paragraph(signature_text, header_style))
    
    # Build PDF
    doc.build(story)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content

def generate_report_pdf(title, data, headers=None):
    """Generate PDF report with tabular data"""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,
    )
    
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 30))
    
    # Data table
    if headers and data:
        table_data = [headers] + data
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
    
    # Build PDF
    doc.build(story)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content
