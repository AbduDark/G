import os
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

from config.settings import app_settings

class PDFGenerator:
    """PDF generator for invoices and reports"""
    
    def __init__(self):
        self.setup_fonts()
        self.output_dir = Path.home() / "Documents" / "الحسيني" / "الفواتير"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_fonts(self):
        """Setup Arabic fonts for PDF generation"""
        try:
            # Try to register Arabic fonts
            font_paths = [
                "C:/Windows/Fonts/arial.ttf",
                "C:/Windows/Fonts/calibri.ttf",
                "assets/fonts/NotoSansArabic-Regular.ttf"
            ]
            
            self.arabic_font = "Helvetica"  # Default fallback
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        pdfmetrics.registerFont(TTFont('Arabic', font_path))
                        self.arabic_font = 'Arabic'
                        break
                    except:
                        continue
                        
        except Exception as e:
            print(f"Font setup error: {e}")
            self.arabic_font = "Helvetica"
    
    def generate_invoice_pdf(self, sale):
        """Generate PDF invoice for a sale"""
        try:
            # Create filename
            filename = f"فاتورة_{sale.invoice_no}.pdf"
            filepath = self.output_dir / filename
            
            # Create document
            doc = SimpleDocTemplate(
                str(filepath),
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            # Build content
            story = []
            
            # Add header
            story.extend(self._create_header())
            story.append(Spacer(1, 0.5*cm))
            
            # Add invoice info
            story.extend(self._create_invoice_info(sale))
            story.append(Spacer(1, 0.5*cm))
            
            # Add customer info
            if sale.customer:
                story.extend(self._create_customer_info(sale.customer))
                story.append(Spacer(1, 0.5*cm))
            
            # Add items table
            story.extend(self._create_items_table(sale.sale_items))
            story.append(Spacer(1, 0.5*cm))
            
            # Add totals
            story.extend(self._create_totals_section(sale))
            story.append(Spacer(1, 1*cm))
            
            # Add footer
            story.extend(self._create_footer())
            
            # Build PDF
            doc.build(story)
            
            return str(filepath)
            
        except Exception as e:
            raise Exception(f"خطأ في إنشاء ملف PDF: {str(e)}")
    
    def _create_header(self):
        """Create PDF header with shop info"""
        elements = []
        
        # Shop name
        shop_name = app_settings.get('shop_info.name', 'محل الحسيني')
        title_style = ParagraphStyle(
            'Title',
            parent=getSampleStyleSheet()['Title'],
            fontName=self.arabic_font,
            fontSize=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        elements.append(Paragraph(shop_name, title_style))
        
        # Shop info
        shop_info = []
        address = app_settings.get('shop_info.address', '')
        phone = app_settings.get('shop_info.phone', '')
        email = app_settings.get('shop_info.email', '')
        
        if address:
            shop_info.append(f"العنوان: {address}")
        if phone:
            shop_info.append(f"الهاتف: {phone}")
        if email:
            shop_info.append(f"البريد: {email}")
        
        if shop_info:
            info_style = ParagraphStyle(
                'Info',
                parent=getSampleStyleSheet()['Normal'],
                fontName=self.arabic_font,
                fontSize=10,
                alignment=TA_CENTER
            )
            elements.append(Paragraph(" | ".join(shop_info), info_style))
        
        return elements
    
    def _create_invoice_info(self, sale):
        """Create invoice information section"""
        elements = []
        
        # Invoice title
        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=getSampleStyleSheet()['Heading2'],
            fontName=self.arabic_font,
            fontSize=16,
            alignment=TA_CENTER,
            textColor=colors.black
        )
        elements.append(Paragraph("فاتورة مبيعات", title_style))
        
        # Invoice details table
        invoice_data = [
            ["رقم الفاتورة:", sale.invoice_no],
            ["التاريخ:", sale.created_at.strftime("%Y-%m-%d")],
            ["الوقت:", sale.created_at.strftime("%H:%M:%S")],
            ["المستخدم:", sale.user.name if sale.user else ""]
        ]
        
        invoice_table = Table(invoice_data, colWidths=[3*cm, 5*cm])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.arabic_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey)
        ]))
        
        elements.append(invoice_table)
        return elements
    
    def _create_customer_info(self, customer):
        """Create customer information section"""
        elements = []
        
        customer_data = [
            ["اسم العميل:", customer.name],
            ["رقم الهاتف:", customer.phone or "غير محدد"],
            ["العنوان:", customer.address or "غير محدد"]
        ]
        
        customer_table = Table(customer_data, colWidths=[3*cm, 8*cm])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.arabic_font),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightyellow)
        ]))
        
        elements.append(customer_table)
        return elements
    
    def _create_items_table(self, sale_items):
        """Create items table"""
        elements = []
        
        # Table headers
        headers = ["المنتج", "الكمية", "سعر الوحدة", "الإجمالي"]
        
        # Table data
        table_data = [headers]
        
        for item in sale_items:
            row = [
                item.product.name_ar,
                str(item.quantity),
                f"{item.unit_price:.2f}",
                f"{item.line_total:.2f}"
            ]
            table_data.append(row)
        
        # Create table
        items_table = Table(table_data, colWidths=[6*cm, 2*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), self.arabic_font),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('FONTWEIGHT', (0, 0), (-1, 0), 'BOLD'),
            
            # Data rows style
            ('FONTNAME', (0, 1), (-1, -1), self.arabic_font),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        
        elements.append(items_table)
        return elements
    
    def _create_totals_section(self, sale):
        """Create totals section"""
        elements = []
        
        currency = app_settings.get('invoice.currency', 'جنيه')
        
        # Totals data
        totals_data = [
            ["المجموع الفرعي:", f"{sale.subtotal:.2f} {currency}"],
            ["الخصم:", f"{sale.discount:.2f} {currency}"],
            ["الضريبة:", f"{sale.tax:.2f} {currency}"],
            ["الإجمالي:", f"{sale.total:.2f} {currency}"],
            ["المدفوع:", f"{sale.paid:.2f} {currency}"],
            ["الباقي:", f"{sale.change:.2f} {currency}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[4*cm, 4*cm])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.arabic_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Highlight total row
            ('BACKGROUND', (0, 3), (-1, 3), colors.lightblue),
            ('FONTSIZE', (0, 3), (-1, 3), 12),
            ('FONTWEIGHT', (0, 3), (-1, 3), 'BOLD')
        ]))
        
        elements.append(totals_table)
        return elements
    
    def _create_footer(self):
        """Create PDF footer"""
        elements = []
        
        footer_text = app_settings.get('invoice.footer_text', 'شكراً لتعاملكم معنا')
        
        if footer_text:
            footer_style = ParagraphStyle(
                'Footer',
                parent=getSampleStyleSheet()['Normal'],
                fontName=self.arabic_font,
                fontSize=10,
                alignment=TA_CENTER,
                textColor=colors.grey
            )
            elements.append(Paragraph(footer_text, footer_style))
        
        # Add generation timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp_style = ParagraphStyle(
            'Timestamp',
            parent=getSampleStyleSheet()['Normal'],
            fontName=self.arabic_font,
            fontSize=8,
            alignment=TA_CENTER,
            textColor=colors.lightgrey
        )
        elements.append(Paragraph(f"تم إنشاء الفاتورة في: {timestamp}", timestamp_style))
        
        return elements
    
    def generate_repair_receipt(self, repair):
        """Generate repair service receipt"""
        try:
            filename = f"إيصال_صيانة_{repair.ticket_no}.pdf"
            filepath = self.output_dir / filename
            
            doc = SimpleDocTemplate(str(filepath), pagesize=A4)
            story = []
            
            # Header
            story.extend(self._create_header())
            story.append(Spacer(1, 0.5*cm))
            
            # Receipt title
            title_style = ParagraphStyle(
                'ReceiptTitle',
                parent=getSampleStyleSheet()['Heading2'],
                fontName=self.arabic_font,
                fontSize=16,
                alignment=TA_CENTER
            )
            story.append(Paragraph("إيصال استلام جهاز للصيانة", title_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Repair details
            repair_data = [
                ["رقم التذكرة:", repair.ticket_no],
                ["العميل:", repair.customer.name if repair.customer else "غير محدد"],
                ["رقم الهاتف:", repair.customer.phone if repair.customer and repair.customer.phone else "غير محدد"],
                ["نوع الجهاز:", repair.device_model],
                ["وصف المشكلة:", repair.problem_desc],
                ["تاريخ الاستلام:", repair.entry_date.strftime("%Y-%m-%d %H:%M")],
                ["الحالة:", repair.status],
                ["تكلفة القطع:", f"{repair.parts_cost:.2f} جنيه"],
                ["تكلفة العمالة:", f"{repair.labor_cost:.2f} جنيه"],
                ["التكلفة الإجمالية:", f"{repair.total_cost:.2f} جنيه"]
            ]
            
            repair_table = Table(repair_data, colWidths=[4*cm, 8*cm])
            repair_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), self.arabic_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
            ]))
            
            story.append(repair_table)
            story.append(Spacer(1, 1*cm))
            
            # Notes
            if repair.notes:
                story.append(Paragraph("ملاحظات:", getSampleStyleSheet()['Heading3']))
                story.append(Paragraph(repair.notes, getSampleStyleSheet()['Normal']))
            
            # Footer
            story.extend(self._create_footer())
            
            doc.build(story)
            return str(filepath)
            
        except Exception as e:
            raise Exception(f"خطأ في إنشاء إيصال الصيانة: {str(e)}")
    
    def generate_report_pdf(self, report_type, data):
        """Generate report PDF"""
        try:
            filename = f"تقرير_{report_type}_{datetime.now().strftime('%Y%m%d')}.pdf"
            filepath = self.output_dir / filename
            
            doc = SimpleDocTemplate(str(filepath), pagesize=A4)
            story = []
            
            # Header
            story.extend(self._create_header())
            story.append(Spacer(1, 0.5*cm))
            
            # Report title
            title_style = ParagraphStyle(
                'ReportTitle',
                parent=getSampleStyleSheet()['Heading2'],
                fontName=self.arabic_font,
                fontSize=16,
                alignment=TA_CENTER
            )
            story.append(Paragraph(f"تقرير {report_type}", title_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Report content (customize based on report type)
            if report_type == "المبيعات":
                story.extend(self._create_sales_report_content(data))
            elif report_type == "المخزون":
                story.extend(self._create_inventory_report_content(data))
            
            # Footer
            story.extend(self._create_footer())
            
            doc.build(story)
            return str(filepath)
            
        except Exception as e:
            raise Exception(f"خطأ في إنشاء تقرير PDF: {str(e)}")
    
    def _create_sales_report_content(self, data):
        """Create sales report content"""
        elements = []
        
        # Summary
        summary_data = [
            ["إجمالي المبيعات:", f"{data.get('total_sales', 0):.2f} جنيه"],
            ["عدد المعاملات:", str(data.get('total_transactions', 0))],
            ["متوسط المعاملة:", f"{data.get('average_transaction', 0):.2f} جنيه"]
        ]
        
        summary_table = Table(summary_data, colWidths=[4*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.arabic_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightblue)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
    
    def _create_inventory_report_content(self, data):
        """Create inventory report content"""
        elements = []
        
        # Inventory summary
        summary_data = [
            ["إجمالي المنتجات:", str(data.get('total_products', 0))],
            ["منتجات منخفضة المخزون:", str(data.get('low_stock', 0))],
            ["منتجات نفدت:", str(data.get('out_of_stock', 0))],
            ["قيمة المخزون:", f"{data.get('total_value', 0):.2f} جنيه"]
        ]
        
        summary_table = Table(summary_data, colWidths=[4*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), self.arabic_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, -1), colors.lightgreen)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 0.5*cm))
        
        return elements
