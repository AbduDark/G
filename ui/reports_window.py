# -*- coding: utf-8 -*-
"""
Reports and analytics window
"""

import logging
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                            QLineEdit, QComboBox, QDateEdit, QTextEdit,
                            QMessageBox, QHeaderView, QFrame, QGroupBox,
                            QFormLayout, QTabWidget, QSplitter, QScrollArea,
                            QProgressBar, QCheckBox)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QThread
from PyQt6.QtGui import QFont, QColor, QPixmap
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from models.user import User
from config.database import get_db_session
from services.report_service import ReportService
from utils.helpers import format_currency, show_error, show_success, export_to_excel

class ReportsWindow(QMainWindow):
    """Reports and analytics window"""
    
    def __init__(self, user: User):
        super().__init__()
        self.current_user = user
        self.report_service = ReportService()
        
        self.setup_ui()
        self.setup_connections()
        self.load_initial_data()
        
    def setup_ui(self):
        """Setup user interface"""
        self.setWindowTitle("التقارير والإحصائيات")
        self.setMinimumSize(1400, 900)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Dashboard tab
        self.setup_dashboard_tab()
        
        # Sales reports tab
        self.setup_sales_reports_tab()
        
        # Inventory reports tab
        self.setup_inventory_reports_tab()
        
        # Repair reports tab
        self.setup_repair_reports_tab()
        
        # Transfer reports tab
        self.setup_transfer_reports_tab()
        
        # Financial reports tab
        self.setup_financial_reports_tab()
        
    def setup_dashboard_tab(self):
        """Setup dashboard tab with overview charts"""
        dashboard_widget = QWidget()
        layout = QVBoxLayout()
        
        # Date range selector
        date_range_layout = QHBoxLayout()
        
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        self.date_from.setCalendarPopup(True)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        
        self.refresh_dashboard_btn = QPushButton("تحديث اللوحة")
        
        date_range_layout.addWidget(QLabel("من تاريخ:"))
        date_range_layout.addWidget(self.date_from)
        date_range_layout.addWidget(QLabel("إلى تاريخ:"))
        date_range_layout.addWidget(self.date_to)
        date_range_layout.addWidget(self.refresh_dashboard_btn)
        date_range_layout.addStretch()
        
        layout.addLayout(date_range_layout)
        
        # Key metrics cards
        metrics_layout = QHBoxLayout()
        
        # Today's sales card
        self.today_sales_card = self.create_metric_card("مبيعات اليوم", "0 ج.م", "#28a745")
        # Monthly sales card
        self.monthly_sales_card = self.create_metric_card("مبيعات الشهر", "0 ج.م", "#007bff")
        # Total profit card
        self.profit_card = self.create_metric_card("صافي الربح", "0 ج.م", "#17a2b8")
        # Low stock items card
        self.low_stock_card = self.create_metric_card("منتجات منخفضة", "0", "#ffc107")
        
        metrics_layout.addWidget(self.today_sales_card)
        metrics_layout.addWidget(self.monthly_sales_card)
        metrics_layout.addWidget(self.profit_card)
        metrics_layout.addWidget(self.low_stock_card)
        
        layout.addLayout(metrics_layout)
        
        # Charts section
        charts_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sales trend chart
        sales_chart_widget = QWidget()
        sales_chart_layout = QVBoxLayout()
        sales_chart_layout.addWidget(QLabel("اتجاه المبيعات الشهرية"))
        
        self.sales_chart = self.create_chart_widget()
        sales_chart_layout.addWidget(self.sales_chart)
        sales_chart_widget.setLayout(sales_chart_layout)
        
        # Top products chart
        products_chart_widget = QWidget()
        products_chart_layout = QVBoxLayout()
        products_chart_layout.addWidget(QLabel("أكثر المنتجات مبيعاً"))
        
        self.products_chart = self.create_chart_widget()
        products_chart_layout.addWidget(self.products_chart)
        products_chart_widget.setLayout(products_chart_layout)
        
        charts_splitter.addWidget(sales_chart_widget)
        charts_splitter.addWidget(products_chart_widget)
        
        layout.addWidget(charts_splitter)
        
        dashboard_widget.setLayout(layout)
        self.tab_widget.addTab(dashboard_widget, "لوحة المعلومات")
        
    def setup_sales_reports_tab(self):
        """Setup sales reports tab"""
        sales_widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        self.sales_date_from = QDateEdit()
        self.sales_date_from.setDate(QDate.currentDate().addDays(-30))
        self.sales_date_from.setCalendarPopup(True)
        
        self.sales_date_to = QDateEdit()
        self.sales_date_to.setDate(QDate.currentDate())
        self.sales_date_to.setCalendarPopup(True)
        
        self.sales_user_filter = QComboBox()
        self.sales_user_filter.addItem("جميع المستخدمين", None)
        
        self.generate_sales_report_btn = QPushButton("إنشاء التقرير")
        self.export_sales_btn = QPushButton("تصدير Excel")
        
        filter_layout.addWidget(QLabel("من:"))
        filter_layout.addWidget(self.sales_date_from)
        filter_layout.addWidget(QLabel("إلى:"))
        filter_layout.addWidget(self.sales_date_to)
        filter_layout.addWidget(QLabel("المستخدم:"))
        filter_layout.addWidget(self.sales_user_filter)
        filter_layout.addWidget(self.generate_sales_report_btn)
        filter_layout.addWidget(self.export_sales_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Sales summary
        summary_layout = QHBoxLayout()
        
        self.sales_summary_labels = {
            'total_sales': QLabel("إجمالي المبيعات: 0 ج.م"),
            'total_invoices': QLabel("عدد الفواتير: 0"),
            'average_invoice': QLabel("متوسط الفاتورة: 0 ج.م"),
            'total_profit': QLabel("إجمالي الربح: 0 ج.م")
        }
        
        for label in self.sales_summary_labels.values():
            label.setFont(QFont("Cairo", 11, QFont.Weight.Bold))
            summary_layout.addWidget(label)
        
        layout.addLayout(summary_layout)
        
        # Sales table
        self.sales_report_table = QTableWidget()
        self.sales_report_table.setColumnCount(8)
        self.sales_report_table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "التاريخ", "العميل", "إجمالي الفاتورة",
            "الخصم", "الضريبة", "المستخدم", "الربح"
        ])
        
        header = self.sales_report_table.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.sales_report_table)
        
        sales_widget.setLayout(layout)
        self.tab_widget.addTab(sales_widget, "تقارير المبيعات")
        
    def setup_inventory_reports_tab(self):
        """Setup inventory reports tab"""
        inventory_widget = QWidget()
        layout = QVBoxLayout()
        
        # Report type selector
        report_type_layout = QHBoxLayout()
        
        self.inventory_report_type = QComboBox()
        self.inventory_report_type.addItem("تقرير المخزون الحالي", "current_stock")
        self.inventory_report_type.addItem("المنتجات المنخفضة", "low_stock")
        self.inventory_report_type.addItem("حركة المخزون", "stock_movements")
        self.inventory_report_type.addItem("أكثر المنتجات مبيعاً", "top_selling")
        self.inventory_report_type.addItem("المنتجات غير المباعة", "non_selling")
        
        self.generate_inventory_report_btn = QPushButton("إنشاء التقرير")
        self.export_inventory_btn = QPushButton("تصدير Excel")
        
        report_type_layout.addWidget(QLabel("نوع التقرير:"))
        report_type_layout.addWidget(self.inventory_report_type)
        report_type_layout.addWidget(self.generate_inventory_report_btn)
        report_type_layout.addWidget(self.export_inventory_btn)
        report_type_layout.addStretch()
        
        layout.addLayout(report_type_layout)
        
        # Inventory table
        self.inventory_report_table = QTableWidget()
        layout.addWidget(self.inventory_report_table)
        
        inventory_widget.setLayout(layout)
        self.tab_widget.addTab(inventory_widget, "تقارير المخزون")
        
    def setup_repair_reports_tab(self):
        """Setup repair reports tab"""
        repair_widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        self.repair_date_from = QDateEdit()
        self.repair_date_from.setDate(QDate.currentDate().addDays(-30))
        self.repair_date_from.setCalendarPopup(True)
        
        self.repair_date_to = QDateEdit()
        self.repair_date_to.setDate(QDate.currentDate())
        self.repair_date_to.setCalendarPopup(True)
        
        self.repair_status_filter = QComboBox()
        self.repair_status_filter.addItem("جميع الحالات", None)
        self.repair_status_filter.addItem("تم الاستلام", "received")
        self.repair_status_filter.addItem("قيد الإصلاح", "in_progress")
        self.repair_status_filter.addItem("تم الإصلاح", "completed")
        self.repair_status_filter.addItem("تم التسليم", "delivered")
        
        self.generate_repair_report_btn = QPushButton("إنشاء التقرير")
        self.export_repair_btn = QPushButton("تصدير Excel")
        
        filter_layout.addWidget(QLabel("من:"))
        filter_layout.addWidget(self.repair_date_from)
        filter_layout.addWidget(QLabel("إلى:"))
        filter_layout.addWidget(self.repair_date_to)
        filter_layout.addWidget(QLabel("الحالة:"))
        filter_layout.addWidget(self.repair_status_filter)
        filter_layout.addWidget(self.generate_repair_report_btn)
        filter_layout.addWidget(self.export_repair_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Repair table
        self.repair_report_table = QTableWidget()
        self.repair_report_table.setColumnCount(9)
        self.repair_report_table.setHorizontalHeaderLabels([
            "رقم التذكرة", "العميل", "الجهاز", "تاريخ الاستلام",
            "تاريخ التسليم", "الحالة", "التكلفة", "الفني", "الأيام"
        ])
        
        layout.addWidget(self.repair_report_table)
        
        repair_widget.setLayout(layout)
        self.tab_widget.addTab(repair_widget, "تقارير الصيانة")
        
    def setup_transfer_reports_tab(self):
        """Setup transfer reports tab"""
        transfer_widget = QWidget()
        layout = QVBoxLayout()
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        self.transfer_date_from = QDateEdit()
        self.transfer_date_from.setDate(QDate.currentDate().addDays(-30))
        self.transfer_date_from.setCalendarPopup(True)
        
        self.transfer_date_to = QDateEdit()
        self.transfer_date_to.setDate(QDate.currentDate())
        self.transfer_date_to.setCalendarPopup(True)
        
        self.transfer_type_filter = QComboBox()
        self.transfer_type_filter.addItem("جميع الأنواع", None)
        self.transfer_type_filter.addItem("فودافون كاش", "vodafone_cash")
        self.transfer_type_filter.addItem("اتصالات كاش", "etisalat_cash")
        self.transfer_type_filter.addItem("اورانج كاش", "orange_cash")
        
        self.generate_transfer_report_btn = QPushButton("إنشاء التقرير")
        self.export_transfer_btn = QPushButton("تصدير Excel")
        
        filter_layout.addWidget(QLabel("من:"))
        filter_layout.addWidget(self.transfer_date_from)
        filter_layout.addWidget(QLabel("إلى:"))
        filter_layout.addWidget(self.transfer_date_to)
        filter_layout.addWidget(QLabel("النوع:"))
        filter_layout.addWidget(self.transfer_type_filter)
        filter_layout.addWidget(self.generate_transfer_report_btn)
        filter_layout.addWidget(self.export_transfer_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # Transfer summary
        transfer_summary_layout = QHBoxLayout()
        
        self.transfer_summary_labels = {
            'total_amount': QLabel("إجمالي المبلغ: 0 ج.م"),
            'total_commission': QLabel("إجمالي العمولة: 0 ج.م"),
            'total_profit': QLabel("إجمالي الربح: 0 ج.م"),
            'transaction_count': QLabel("عدد المعاملات: 0")
        }
        
        for label in self.transfer_summary_labels.values():
            label.setFont(QFont("Cairo", 11, QFont.Weight.Bold))
            transfer_summary_layout.addWidget(label)
        
        layout.addLayout(transfer_summary_layout)
        
        # Transfer table
        self.transfer_report_table = QTableWidget()
        self.transfer_report_table.setColumnCount(8)
        self.transfer_report_table.setHorizontalHeaderLabels([
            "رقم المعاملة", "نوع الخدمة", "المبلغ", "العمولة",
            "الربح", "رقم الهاتف", "التاريخ", "المستخدم"
        ])
        
        layout.addWidget(self.transfer_report_table)
        
        transfer_widget.setLayout(layout)
        self.tab_widget.addTab(transfer_widget, "تقارير التحويلات")
        
    def setup_financial_reports_tab(self):
        """Setup financial reports tab"""
        financial_widget = QWidget()
        layout = QVBoxLayout()
        
        # Report type selector
        report_type_layout = QHBoxLayout()
        
        self.financial_report_type = QComboBox()
        self.financial_report_type.addItem("تقرير الأرباح والخسائر", "profit_loss")
        self.financial_report_type.addItem("تقرير الإيرادات", "revenue")
        self.financial_report_type.addItem("تقرير التكاليف", "costs")
        self.financial_report_type.addItem("تقرير شامل", "comprehensive")
        
        self.financial_date_from = QDateEdit()
        self.financial_date_from.setDate(QDate.currentDate().addDays(-30))
        self.financial_date_from.setCalendarPopup(True)
        
        self.financial_date_to = QDateEdit()
        self.financial_date_to.setDate(QDate.currentDate())
        self.financial_date_to.setCalendarPopup(True)
        
        self.generate_financial_report_btn = QPushButton("إنشاء التقرير")
        self.export_financial_btn = QPushButton("تصدير Excel")
        
        report_type_layout.addWidget(QLabel("نوع التقرير:"))
        report_type_layout.addWidget(self.financial_report_type)
        report_type_layout.addWidget(QLabel("من:"))
        report_type_layout.addWidget(self.financial_date_from)
        report_type_layout.addWidget(QLabel("إلى:"))
        report_type_layout.addWidget(self.financial_date_to)
        report_type_layout.addWidget(self.generate_financial_report_btn)
        report_type_layout.addWidget(self.export_financial_btn)
        report_type_layout.addStretch()
        
        layout.addLayout(report_type_layout)
        
        # Financial summary
        financial_summary_group = QGroupBox("الملخص المالي")
        financial_summary_layout = QFormLayout()
        
        self.financial_summary_labels = {
            'total_revenue': QLabel("0 ج.م"),
            'total_costs': QLabel("0 ج.م"),
            'gross_profit': QLabel("0 ج.م"),
            'net_profit': QLabel("0 ج.م"),
            'profit_margin': QLabel("0%")
        }
        
        financial_summary_layout.addRow("إجمالي الإيرادات:", self.financial_summary_labels['total_revenue'])
        financial_summary_layout.addRow("إجمالي التكاليف:", self.financial_summary_labels['total_costs'])
        financial_summary_layout.addRow("إجمالي الربح:", self.financial_summary_labels['gross_profit'])
        financial_summary_layout.addRow("صافي الربح:", self.financial_summary_labels['net_profit'])
        financial_summary_layout.addRow("هامش الربح:", self.financial_summary_labels['profit_margin'])
        
        financial_summary_group.setLayout(financial_summary_layout)
        layout.addWidget(financial_summary_group)
        
        # Financial chart
        self.financial_chart = self.create_chart_widget()
        layout.addWidget(self.financial_chart)
        
        financial_widget.setLayout(layout)
        self.tab_widget.addTab(financial_widget, "التقارير المالية")
        
    def create_metric_card(self, title: str, value: str, color: str):
        """Create a metric card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setLineWidth(1)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                border-left: 4px solid {color};
                padding: 15px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Cairo", 18, QFont.Weight.Bold))
        value_label.setStyleSheet(f"color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Cairo", 11))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #6c757d;")
        
        layout.addWidget(value_label)
        layout.addWidget(title_label)
        card.setLayout(layout)
        
        # Store labels for updating
        card.value_label = value_label
        card.title_label = title_label
        
        return card
        
    def create_chart_widget(self):
        """Create a matplotlib chart widget"""
        figure = Figure(figsize=(8, 6))
        canvas = FigureCanvas(figure)
        canvas.figure = figure
        return canvas
        
    def setup_connections(self):
        """Setup signal connections"""
        # Dashboard
        self.refresh_dashboard_btn.clicked.connect(self.refresh_dashboard)
        
        # Sales reports
        self.generate_sales_report_btn.clicked.connect(self.generate_sales_report)
        self.export_sales_btn.clicked.connect(self.export_sales_report)
        
        # Inventory reports
        self.generate_inventory_report_btn.clicked.connect(self.generate_inventory_report)
        self.export_inventory_btn.clicked.connect(self.export_inventory_report)
        
        # Repair reports
        self.generate_repair_report_btn.clicked.connect(self.generate_repair_report)
        self.export_repair_btn.clicked.connect(self.export_repair_report)
        
        # Transfer reports
        self.generate_transfer_report_btn.clicked.connect(self.generate_transfer_report)
        self.export_transfer_btn.clicked.connect(self.export_transfer_report)
        
        # Financial reports
        self.generate_financial_report_btn.clicked.connect(self.generate_financial_report)
        self.export_financial_btn.clicked.connect(self.export_financial_report)
        
    def load_initial_data(self):
        """Load initial data for reports"""
        self.load_users_for_filters()
        self.refresh_dashboard()
        
    def load_users_for_filters(self):
        """Load users for filter dropdowns"""
        try:
            users = self.report_service.get_all_users()
            
            for user in users:
                self.sales_user_filter.addItem(user.name, user.id)
                
        except Exception as e:
            logging.error(f"Error loading users for filters: {e}")
            
    def refresh_dashboard(self):
        """Refresh dashboard metrics and charts"""
        try:
            date_from = self.date_from.date().toPython()
            date_to = self.date_to.date().toPython()
            
            # Get dashboard metrics
            metrics = self.report_service.get_dashboard_metrics(date_from, date_to)
            
            # Update metric cards
            self.today_sales_card.value_label.setText(format_currency(metrics.get('today_sales', 0)))
            self.monthly_sales_card.value_label.setText(format_currency(metrics.get('monthly_sales', 0)))
            self.profit_card.value_label.setText(format_currency(metrics.get('total_profit', 0)))
            self.low_stock_card.value_label.setText(str(metrics.get('low_stock_count', 0)))
            
            # Update charts
            self.update_sales_trend_chart(date_from, date_to)
            self.update_top_products_chart(date_from, date_to)
            
        except Exception as e:
            logging.error(f"Error refreshing dashboard: {e}")
            show_error(self, f"خطأ في تحديث لوحة المعلومات:\n{str(e)}")
            
    def update_sales_trend_chart(self, date_from, date_to):
        """Update sales trend chart"""
        try:
            sales_data = self.report_service.get_sales_trend(date_from, date_to)
            
            # Clear previous chart
            self.sales_chart.figure.clear()
            ax = self.sales_chart.figure.add_subplot(111)
            
            if sales_data:
                dates = [item['date'] for item in sales_data]
                amounts = [item['total'] for item in sales_data]
                
                ax.plot(dates, amounts, marker='o', linewidth=2, markersize=6)
                ax.set_title('اتجاه المبيعات اليومية', fontsize=12, fontweight='bold')
                ax.set_xlabel('التاريخ')
                ax.set_ylabel('المبيعات (ج.م)')
                ax.grid(True, alpha=0.3)
                
                # Format dates on x-axis
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
                ax.xaxis.set_major_locator(mdates.WeekdayLocator())
                
            else:
                ax.text(0.5, 0.5, 'لا توجد بيانات', ha='center', va='center', transform=ax.transAxes)
                
            self.sales_chart.draw()
            
        except Exception as e:
            logging.error(f"Error updating sales trend chart: {e}")
            
    def update_top_products_chart(self, date_from, date_to):
        """Update top products chart"""
        try:
            products_data = self.report_service.get_top_selling_products(date_from, date_to, limit=10)
            
            # Clear previous chart
            self.products_chart.figure.clear()
            ax = self.products_chart.figure.add_subplot(111)
            
            if products_data:
                products = [item['product_name'][:20] + '...' if len(item['product_name']) > 20 else item['product_name'] for item in products_data]
                quantities = [item['total_quantity'] for item in products_data]
                
                bars = ax.barh(products, quantities)
                ax.set_title('أكثر المنتجات مبيعاً', fontsize=12, fontweight='bold')
                ax.set_xlabel('الكمية المباعة')
                
                # Color bars
                for bar in bars:
                    bar.set_color('#007bff')
                    
            else:
                ax.text(0.5, 0.5, 'لا توجد بيانات', ha='center', va='center', transform=ax.transAxes)
                
            self.products_chart.draw()
            
        except Exception as e:
            logging.error(f"Error updating top products chart: {e}")
            
    def generate_sales_report(self):
        """Generate sales report"""
        try:
            date_from = self.sales_date_from.date().toPython()
            date_to = self.sales_date_to.date().toPython()
            user_id = self.sales_user_filter.currentData()
            
            # Get sales data
            sales_data = self.report_service.get_sales_report(date_from, date_to, user_id)
            
            # Update table
            self.sales_report_table.setRowCount(len(sales_data['sales']))
            
            for row, sale in enumerate(sales_data['sales']):
                self.sales_report_table.setItem(row, 0, QTableWidgetItem(sale.invoice_no))
                self.sales_report_table.setItem(row, 1, QTableWidgetItem(sale.created_at.strftime("%Y-%m-%d %H:%M")))
                self.sales_report_table.setItem(row, 2, QTableWidgetItem(sale.customer.name if sale.customer else "عميل نقدي"))
                self.sales_report_table.setItem(row, 3, QTableWidgetItem(format_currency(sale.total)))
                self.sales_report_table.setItem(row, 4, QTableWidgetItem(format_currency(sale.discount_amount)))
                self.sales_report_table.setItem(row, 5, QTableWidgetItem(format_currency(sale.tax_amount)))
                self.sales_report_table.setItem(row, 6, QTableWidgetItem(sale.user.name))
                self.sales_report_table.setItem(row, 7, QTableWidgetItem(format_currency(sale.profit)))
            
            # Update summary
            summary = sales_data['summary']
            self.sales_summary_labels['total_sales'].setText(f"إجمالي المبيعات: {format_currency(summary['total_sales'])}")
            self.sales_summary_labels['total_invoices'].setText(f"عدد الفواتير: {summary['total_invoices']}")
            self.sales_summary_labels['average_invoice'].setText(f"متوسط الفاتورة: {format_currency(summary['average_invoice'])}")
            self.sales_summary_labels['total_profit'].setText(f"إجمالي الربح: {format_currency(summary['total_profit'])}")
            
            show_success(self, "تم إنشاء تقرير المبيعات بنجاح")
            
        except Exception as e:
            logging.error(f"Error generating sales report: {e}")
            show_error(self, f"خطأ في إنشاء تقرير المبيعات:\n{str(e)}")
            
    def generate_inventory_report(self):
        """Generate inventory report"""
        try:
            report_type = self.inventory_report_type.currentData()
            
            if report_type == "current_stock":
                data = self.report_service.get_current_stock_report()
                headers = ["SKU", "اسم المنتج", "الفئة", "الكمية الحالية", "سعر الشراء", "سعر البيع", "قيمة المخزون"]
            elif report_type == "low_stock":
                data = self.report_service.get_low_stock_report()
                headers = ["SKU", "اسم المنتج", "الكمية الحالية", "الحد الأدنى", "الفئة"]
            elif report_type == "top_selling":
                data = self.report_service.get_top_selling_products_report()
                headers = ["اسم المنتج", "الكمية المباعة", "إجمالي المبيعات", "متوسط السعر"]
            else:
                show_error(self, "نوع التقرير غير مدعوم")
                return
            
            # Update table
            self.inventory_report_table.setColumnCount(len(headers))
            self.inventory_report_table.setHorizontalHeaderLabels(headers)
            self.inventory_report_table.setRowCount(len(data))
            
            for row, item in enumerate(data):
                for col, value in enumerate(item):
                    self.inventory_report_table.setItem(row, col, QTableWidgetItem(str(value)))
            
            show_success(self, "تم إنشاء تقرير المخزون بنجاح")
            
        except Exception as e:
            logging.error(f"Error generating inventory report: {e}")
            show_error(self, f"خطأ في إنشاء تقرير المخزون:\n{str(e)}")
            
    def generate_repair_report(self):
        """Generate repair report"""
        try:
            date_from = self.repair_date_from.date().toPython()
            date_to = self.repair_date_to.date().toPython()
            status = self.repair_status_filter.currentData()
            
            repairs_data = self.report_service.get_repair_report(date_from, date_to, status)
            
            self.repair_report_table.setRowCount(len(repairs_data))
            
            for row, repair in enumerate(repairs_data):
                self.repair_report_table.setItem(row, 0, QTableWidgetItem(repair.ticket_no))
                self.repair_report_table.setItem(row, 1, QTableWidgetItem(repair.customer.name))
                self.repair_report_table.setItem(row, 2, QTableWidgetItem(repair.device_model))
                self.repair_report_table.setItem(row, 3, QTableWidgetItem(repair.entry_date.strftime("%Y-%m-%d")))
                delivery_date = repair.delivered_date.strftime("%Y-%m-%d") if repair.delivered_date else "-"
                self.repair_report_table.setItem(row, 4, QTableWidgetItem(delivery_date))
                self.repair_report_table.setItem(row, 5, QTableWidgetItem(repair.status))
                total_cost = repair.parts_cost + repair.labor_cost
                self.repair_report_table.setItem(row, 6, QTableWidgetItem(format_currency(total_cost)))
                tech_name = repair.technician.name if repair.technician else "-"
                self.repair_report_table.setItem(row, 7, QTableWidgetItem(tech_name))
                self.repair_report_table.setItem(row, 8, QTableWidgetItem(str(repair.days_in_service)))
            
            show_success(self, "تم إنشاء تقرير الصيانة بنجاح")
            
        except Exception as e:
            logging.error(f"Error generating repair report: {e}")
            show_error(self, f"خطأ في إنشاء تقرير الصيانة:\n{str(e)}")
            
    def generate_transfer_report(self):
        """Generate transfer report"""
        try:
            date_from = self.transfer_date_from.date().toPython()
            date_to = self.transfer_date_to.date().toPython()
            transfer_type = self.transfer_type_filter.currentData()
            
            transfers_data = self.report_service.get_transfer_report(date_from, date_to, transfer_type)
            
            self.transfer_report_table.setRowCount(len(transfers_data['transfers']))
            
            total_amount = 0
            total_commission = 0
            total_profit = 0
            
            for row, transfer in enumerate(transfers_data['transfers']):
                total_amount += transfer.amount
                total_commission += transfer.commission
                total_profit += transfer.profit
                
                self.transfer_report_table.setItem(row, 0, QTableWidgetItem(transfer.transaction_id))
                self.transfer_report_table.setItem(row, 1, QTableWidgetItem(transfer.service_type_ar))
                self.transfer_report_table.setItem(row, 2, QTableWidgetItem(format_currency(transfer.amount)))
                self.transfer_report_table.setItem(row, 3, QTableWidgetItem(format_currency(transfer.commission)))
                self.transfer_report_table.setItem(row, 4, QTableWidgetItem(format_currency(transfer.profit)))
                self.transfer_report_table.setItem(row, 5, QTableWidgetItem(transfer.customer_phone))
                self.transfer_report_table.setItem(row, 6, QTableWidgetItem(transfer.processed_at.strftime("%Y-%m-%d %H:%M")))
                self.transfer_report_table.setItem(row, 7, QTableWidgetItem(transfer.user.name))
            
            # Update summary
            self.transfer_summary_labels['total_amount'].setText(f"إجمالي المبلغ: {format_currency(total_amount)}")
            self.transfer_summary_labels['total_commission'].setText(f"إجمالي العمولة: {format_currency(total_commission)}")
            self.transfer_summary_labels['total_profit'].setText(f"إجمالي الربح: {format_currency(total_profit)}")
            self.transfer_summary_labels['transaction_count'].setText(f"عدد المعاملات: {len(transfers_data['transfers'])}")
            
            show_success(self, "تم إنشاء تقرير التحويلات بنجاح")
            
        except Exception as e:
            logging.error(f"Error generating transfer report: {e}")
            show_error(self, f"خطأ في إنشاء تقرير التحويلات:\n{str(e)}")
            
    def generate_financial_report(self):
        """Generate financial report"""
        try:
            date_from = self.financial_date_from.date().toPython()
            date_to = self.financial_date_to.date().toPython()
            report_type = self.financial_report_type.currentData()
            
            financial_data = self.report_service.get_financial_report(date_from, date_to, report_type)
            
            # Update summary
            summary = financial_data['summary']
            self.financial_summary_labels['total_revenue'].setText(format_currency(summary['total_revenue']))
            self.financial_summary_labels['total_costs'].setText(format_currency(summary['total_costs']))
            self.financial_summary_labels['gross_profit'].setText(format_currency(summary['gross_profit']))
            self.financial_summary_labels['net_profit'].setText(format_currency(summary['net_profit']))
            self.financial_summary_labels['profit_margin'].setText(f"{summary['profit_margin']:.2f}%")
            
            # Update financial chart
            self.update_financial_chart(financial_data['chart_data'])
            
            show_success(self, "تم إنشاء التقرير المالي بنجاح")
            
        except Exception as e:
            logging.error(f"Error generating financial report: {e}")
            show_error(self, f"خطأ في إنشاء التقرير المالي:\n{str(e)}")
            
    def update_financial_chart(self, chart_data):
        """Update financial chart"""
        try:
            self.financial_chart.figure.clear()
            ax = self.financial_chart.figure.add_subplot(111)
            
            if chart_data:
                categories = list(chart_data.keys())
                values = list(chart_data.values())
                
                bars = ax.bar(categories, values, color=['#28a745', '#dc3545', '#007bff'])
                ax.set_title('التحليل المالي', fontsize=12, fontweight='bold')
                ax.set_ylabel('المبلغ (ج.م)')
                
                # Add value labels on bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.0f}', ha='center', va='bottom')
                           
            else:
                ax.text(0.5, 0.5, 'لا توجد بيانات', ha='center', va='center', transform=ax.transAxes)
                
            self.financial_chart.draw()
            
        except Exception as e:
            logging.error(f"Error updating financial chart: {e}")
            
    # Export methods
    def export_sales_report(self):
        """Export sales report to Excel"""
        try:
            # Get current table data
            data = []
            headers = []
            
            # Get headers
            for col in range(self.sales_report_table.columnCount()):
                headers.append(self.sales_report_table.horizontalHeaderItem(col).text())
            
            # Get data
            for row in range(self.sales_report_table.rowCount()):
                row_data = []
                for col in range(self.sales_report_table.columnCount()):
                    item = self.sales_report_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            filename = f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            export_to_excel(data, headers, filename)
            show_success(self, f"تم تصدير التقرير إلى {filename}")
            
        except Exception as e:
            logging.error(f"Error exporting sales report: {e}")
            show_error(self, f"خطأ في تصدير التقرير:\n{str(e)}")
            
    def export_inventory_report(self):
        """Export inventory report to Excel"""
        show_error(self, "ميزة تصدير تقرير المخزون قيد التطوير")
        
    def export_repair_report(self):
        """Export repair report to Excel"""
        show_error(self, "ميزة تصدير تقرير الصيانة قيد التطوير")
        
    def export_transfer_report(self):
        """Export transfer report to Excel"""
        show_error(self, "ميزة تصدير تقرير التحويلات قيد التطوير")
        
    def export_financial_report(self):
        """Export financial report to Excel"""
        show_error(self, "ميزة تصدير التقرير المالي قيد التطوير")
