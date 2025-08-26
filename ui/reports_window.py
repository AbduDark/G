from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                            QLabel, QPushButton, QTableWidget, QTableWidgetItem,
                            QComboBox, QDateEdit, QTextEdit, QTabWidget,
                            QGroupBox, QHeaderView, QAbstractItemView, QSplitter,
                            QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from services.report_service import ReportService
from ui.styles import get_stylesheet
from utils.excel_export import ExcelExporter

class ReportsWindow(QMainWindow):
    """Reports and analytics window"""
    
    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.report_service = ReportService()
        self.excel_exporter = ExcelExporter()
        
        self.setup_ui()
        self.apply_styles()
        self.setup_matplotlib()
    
    def setup_ui(self):
        """Setup the user interface"""
        self.setWindowTitle("التقارير والتحليلات")
        self.setMinimumSize(1400, 800)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("التقارير والتحليلات")
        title_label.setFont(QFont("Noto Sans Arabic", 18, QFont.Weight.Bold))
        title_label.setObjectName("title-label")
        
        # Export button
        self.export_btn = QPushButton("تصدير إلى Excel")
        self.export_btn.clicked.connect(self.export_to_excel)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.export_btn)
        
        # Date range selection
        date_group = QGroupBox("فترة التقرير")
        date_layout = QHBoxLayout()
        
        from_label = QLabel("من تاريخ:")
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        self.from_date.dateChanged.connect(self.refresh_reports)
        
        to_label = QLabel("إلى تاريخ:")
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.dateChanged.connect(self.refresh_reports)
        
        self.refresh_btn = QPushButton("تحديث التقارير")
        self.refresh_btn.clicked.connect(self.refresh_reports)
        
        date_layout.addWidget(from_label)
        date_layout.addWidget(self.from_date)
        date_layout.addWidget(to_label)
        date_layout.addWidget(self.to_date)
        date_layout.addWidget(self.refresh_btn)
        date_layout.addStretch()
        
        date_group.setLayout(date_layout)
        
        # Tab widget for different report types
        self.tabs = QTabWidget()
        
        # Sales report tab
        self.sales_tab = self.create_sales_tab()
        self.tabs.addTab(self.sales_tab, "تقرير المبيعات")
        
        # Profit report tab
        self.profit_tab = self.create_profit_tab()
        self.tabs.addTab(self.profit_tab, "تقرير الأرباح")
        
        # Inventory report tab
        self.inventory_tab = self.create_inventory_tab()
        self.tabs.addTab(self.inventory_tab, "تقرير المخزون")
        
        # Products report tab
        self.products_tab = self.create_products_tab()
        self.tabs.addTab(self.products_tab, "أكثر المنتجات مبيعاً")
        
        # Charts tab
        self.charts_tab = self.create_charts_tab()
        self.tabs.addTab(self.charts_tab, "الرسوم البيانية")
        
        # Add layouts to main layout
        main_layout.addLayout(header_layout)
        main_layout.addWidget(date_group)
        main_layout.addWidget(self.tabs)
        
        central_widget.setLayout(main_layout)
        
        # Load initial data
        self.refresh_reports()
    
    def create_sales_tab(self):
        """Create sales report tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Summary section
        summary_group = QGroupBox("ملخص المبيعات")
        summary_layout = QHBoxLayout()
        
        self.total_sales_label = QLabel("إجمالي المبيعات: 0.00 جنيه")
        self.total_sales_label.setFont(QFont("Noto Sans Arabic", 12, QFont.Weight.Bold))
        
        self.total_transactions_label = QLabel("عدد المعاملات: 0")
        self.average_transaction_label = QLabel("متوسط المعاملة: 0.00 جنيه")
        
        summary_layout.addWidget(self.total_sales_label)
        summary_layout.addWidget(self.total_transactions_label)
        summary_layout.addWidget(self.average_transaction_label)
        summary_layout.addStretch()
        
        summary_group.setLayout(summary_layout)
        
        # Sales table
        self.sales_table = QTableWidget()
        self.setup_sales_table()
        
        layout.addWidget(summary_group)
        layout.addWidget(self.sales_table)
        
        tab.setLayout(layout)
        return tab
    
    def create_profit_tab(self):
        """Create profit report tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Profit summary
        profit_group = QGroupBox("ملخص الأرباح")
        profit_layout = QHBoxLayout()
        
        self.revenue_label = QLabel("الإيرادات: 0.00 جنيه")
        self.revenue_label.setFont(QFont("Noto Sans Arabic", 12, QFont.Weight.Bold))
        
        self.cost_label = QLabel("التكلفة: 0.00 جنيه")
        self.profit_label = QLabel("الربح: 0.00 جنيه")
        self.margin_label = QLabel("هامش الربح: 0.00%")
        
        profit_layout.addWidget(self.revenue_label)
        profit_layout.addWidget(self.cost_label)
        profit_layout.addWidget(self.profit_label)
        profit_layout.addWidget(self.margin_label)
        profit_layout.addStretch()
        
        profit_group.setLayout(profit_layout)
        
        # Profit details text
        self.profit_details = QTextEdit()
        self.profit_details.setReadOnly(True)
        self.profit_details.setMaximumHeight(200)
        
        layout.addWidget(profit_group)
        layout.addWidget(QLabel("تفاصيل الأرباح:"))
        layout.addWidget(self.profit_details)
        
        tab.setLayout(layout)
        return tab
    
    def create_inventory_tab(self):
        """Create inventory report tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Inventory summary
        inv_group = QGroupBox("ملخص المخزون")
        inv_layout = QHBoxLayout()
        
        self.total_products_label = QLabel("إجمالي المنتجات: 0")
        self.low_stock_label = QLabel("منتجات منخفضة: 0")
        self.out_of_stock_label = QLabel("منتجات نفدت: 0")
        self.inventory_value_label = QLabel("قيمة المخزون: 0.00 جنيه")
        
        inv_layout.addWidget(self.total_products_label)
        inv_layout.addWidget(self.low_stock_label)
        inv_layout.addWidget(self.out_of_stock_label)
        inv_layout.addWidget(self.inventory_value_label)
        inv_layout.addStretch()
        
        inv_group.setLayout(inv_layout)
        
        # Inventory table
        self.inventory_table = QTableWidget()
        self.setup_inventory_table()
        
        layout.addWidget(inv_group)
        layout.addWidget(self.inventory_table)
        
        tab.setLayout(layout)
        return tab
    
    def create_products_tab(self):
        """Create top products tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Top products table
        products_label = QLabel("أكثر المنتجات مبيعاً")
        products_label.setFont(QFont("Noto Sans Arabic", 14, QFont.Weight.Bold))
        
        self.products_table = QTableWidget()
        self.setup_products_table()
        
        layout.addWidget(products_label)
        layout.addWidget(self.products_table)
        
        tab.setLayout(layout)
        return tab
    
    def create_charts_tab(self):
        """Create charts tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Chart controls
        controls_layout = QHBoxLayout()
        
        chart_label = QLabel("نوع المخطط:")
        self.chart_type = QComboBox()
        self.chart_type.addItems(["مبيعات يومية", "مبيعات شهرية", "أكثر المنتجات مبيعاً"])
        self.chart_type.currentTextChanged.connect(self.update_chart)
        
        controls_layout.addWidget(chart_label)
        controls_layout.addWidget(self.chart_type)
        controls_layout.addStretch()
        
        # Matplotlib canvas
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        
        layout.addLayout(controls_layout)
        layout.addWidget(self.canvas)
        
        tab.setLayout(layout)
        return tab
    
    def setup_sales_table(self):
        """Setup sales table"""
        headers = ["رقم الفاتورة", "التاريخ", "العميل", "الإجمالي", "المدفوع", "الباقي"]
        
        self.sales_table.setColumnCount(len(headers))
        self.sales_table.setHorizontalHeaderLabels(headers)
        
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.sales_table.setAlternatingRowColors(True)
        
        # Resize columns
        header = self.sales_table.horizontalHeader()
        header.setStretchLastSection(True)
    
    def setup_inventory_table(self):
        """Setup inventory table"""
        headers = ["اسم المنتج", "الكمية", "الحد الأدنى", "الحالة", "قيمة الكمية"]
        
        self.inventory_table.setColumnCount(len(headers))
        self.inventory_table.setHorizontalHeaderLabels(headers)
        
        self.inventory_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.inventory_table.setAlternatingRowColors(True)
        
        # Resize columns
        header = self.inventory_table.horizontalHeader()
        header.setStretchLastSection(True)
    
    def setup_products_table(self):
        """Setup top products table"""
        headers = ["اسم المنتج", "الكمية المباعة", "إجمالي الإيرادات"]
        
        self.products_table.setColumnCount(len(headers))
        self.products_table.setHorizontalHeaderLabels(headers)
        
        self.products_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.products_table.setAlternatingRowColors(True)
        
        # Resize columns
        header = self.products_table.horizontalHeader()
        header.setStretchLastSection(True)
    
    def apply_styles(self):
        """Apply custom styles"""
        self.setStyleSheet(get_stylesheet("light"))
    
    def setup_matplotlib(self):
        """Setup matplotlib for Arabic support"""
        plt.rcParams['font.family'] = ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def refresh_reports(self):
        """Refresh all reports with current date range"""
        try:
            from_date = self.from_date.date().toPython()
            to_date = self.to_date.date().toPython()
            
            # Convert to datetime for database query
            from_datetime = datetime.combine(from_date, datetime.min.time())
            to_datetime = datetime.combine(to_date, datetime.max.time())
            
            # Load sales report
            self.load_sales_report(from_datetime, to_datetime)
            
            # Load profit report
            self.load_profit_report(from_datetime, to_datetime)
            
            # Load inventory report
            self.load_inventory_report()
            
            # Load top products
            self.load_top_products(from_datetime, to_datetime)
            
            # Update chart
            self.update_chart()
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحديث التقارير: {str(e)}")
    
    def load_sales_report(self, from_date, to_date):
        """Load sales report data"""
        try:
            report_data = self.report_service.get_sales_report(from_date, to_date)
            
            # Update summary
            self.total_sales_label.setText(f"إجمالي المبيعات: {report_data['total_sales']:.2f} جنيه")
            self.total_transactions_label.setText(f"عدد المعاملات: {report_data['total_transactions']}")
            self.average_transaction_label.setText(f"متوسط المعاملة: {report_data['average_transaction']:.2f} جنيه")
            
            # Load sales table
            sales = report_data['sales']
            self.sales_table.setRowCount(len(sales))
            
            for row, sale in enumerate(sales):
                items = [
                    sale.invoice_no,
                    sale.created_at.strftime("%Y-%m-%d %H:%M"),
                    sale.customer.name if sale.customer else "عميل نقدي",
                    f"{sale.total:.2f}",
                    f"{sale.paid:.2f}",
                    f"{sale.change:.2f}"
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    self.sales_table.setItem(row, col, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل تقرير المبيعات: {str(e)}")
    
    def load_profit_report(self, from_date, to_date):
        """Load profit report data"""
        try:
            profit_data = self.report_service.get_profit_report(from_date, to_date)
            
            # Update labels
            self.revenue_label.setText(f"الإيرادات: {profit_data['total_revenue']:.2f} جنيه")
            self.cost_label.setText(f"التكلفة: {profit_data['total_cost']:.2f} جنيه")
            self.profit_label.setText(f"الربح: {profit_data['profit']:.2f} جنيه")
            self.margin_label.setText(f"هامش الربح: {profit_data['margin']:.2f}%")
            
            # Update details
            details = f"""
تفاصيل تقرير الأرباح:
إجمالي الإيرادات: {profit_data['total_revenue']:.2f} جنيه
إجمالي التكلفة: {profit_data['total_cost']:.2f} جنيه
صافي الربح: {profit_data['profit']:.2f} جنيه
هامش الربح: {profit_data['margin']:.2f}%

هذا التقرير يعتمد على أسعار الشراء المسجلة في النظام.
            """
            self.profit_details.setText(details.strip())
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل تقرير الأرباح: {str(e)}")
    
    def load_inventory_report(self):
        """Load inventory report data"""
        try:
            inventory_data = self.report_service.get_inventory_report()
            
            # Update summary
            self.total_products_label.setText(f"إجمالي المنتجات: {inventory_data['total_products']}")
            self.low_stock_label.setText(f"منتجات منخفضة: {inventory_data['low_stock']}")
            self.out_of_stock_label.setText(f"منتجات نفدت: {inventory_data['out_of_stock']}")
            self.inventory_value_label.setText(f"قيمة المخزون: {inventory_data['total_value']:.2f} جنيه")
            
            # Load inventory table
            products = inventory_data['products']
            self.inventory_table.setRowCount(len(products))
            
            for row, product in enumerate(products):
                # Determine stock status
                if product.quantity <= 0:
                    status = "نفد"
                elif product.quantity <= product.min_quantity:
                    status = "منخفض"
                else:
                    status = "متوفر"
                
                value = product.cost_price * product.quantity
                
                items = [
                    product.name_ar,
                    str(product.quantity),
                    str(product.min_quantity),
                    status,
                    f"{value:.2f}"
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    
                    # Color coding
                    if col == 3:  # Status column
                        if status == "نفد":
                            item.setBackground(Qt.GlobalColor.red)
                        elif status == "منخفض":
                            item.setBackground(Qt.GlobalColor.yellow)
                    
                    self.inventory_table.setItem(row, col, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل تقرير المخزون: {str(e)}")
    
    def load_top_products(self, from_date, to_date):
        """Load top selling products"""
        try:
            top_products = self.report_service.get_top_selling_products(10, from_date, to_date)
            
            self.products_table.setRowCount(len(top_products))
            
            for row, (name, total_sold, total_revenue) in enumerate(top_products):
                items = [
                    name,
                    str(total_sold),
                    f"{float(total_revenue):.2f}"
                ]
                
                for col, item_text in enumerate(items):
                    item = QTableWidgetItem(str(item_text))
                    self.products_table.setItem(row, col, item)
                    
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تحميل أكثر المنتجات مبيعاً: {str(e)}")
    
    def update_chart(self):
        """Update chart based on selected type"""
        try:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            chart_type = self.chart_type.currentText()
            
            if chart_type == "مبيعات يومية":
                self.create_daily_sales_chart(ax)
            elif chart_type == "مبيعات شهرية":
                self.create_monthly_sales_chart(ax)
            elif chart_type == "أكثر المنتجات مبيعاً":
                self.create_top_products_chart(ax)
            
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error updating chart: {e}")
    
    def create_daily_sales_chart(self, ax):
        """Create daily sales chart"""
        try:
            sales_data = self.report_service.get_daily_sales_chart_data(30)
            
            if not sales_data:
                ax.text(0.5, 0.5, 'لا توجد بيانات', ha='center', va='center', transform=ax.transAxes)
                return
            
            dates = [datetime.strptime(item['date'], '%Y-%m-%d') for item in sales_data]
            totals = [item['total'] for item in sales_data]
            
            ax.plot(dates, totals, marker='o', linewidth=2, markersize=6)
            ax.set_title('المبيعات اليومية')
            ax.set_xlabel('التاريخ')
            ax.set_ylabel('المبيعات (جنيه)')
            ax.grid(True, alpha=0.3)
            
            # Format dates on x-axis
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.WeekdayLocator())
            self.figure.autofmt_xdate()
            
        except Exception as e:
            ax.text(0.5, 0.5, f'خطأ في عرض البيانات: {str(e)}', ha='center', va='center', transform=ax.transAxes)
    
    def create_monthly_sales_chart(self, ax):
        """Create monthly sales chart"""
        # This would require additional data aggregation
        ax.text(0.5, 0.5, 'مخطط المبيعات الشهرية\n(قيد التطوير)', ha='center', va='center', transform=ax.transAxes)
    
    def create_top_products_chart(self, ax):
        """Create top products chart"""
        try:
            from_date = datetime.combine(self.from_date.date().toPython(), datetime.min.time())
            to_date = datetime.combine(self.to_date.date().toPython(), datetime.max.time())
            
            top_products = self.report_service.get_top_selling_products(10, from_date, to_date)
            
            if not top_products:
                ax.text(0.5, 0.5, 'لا توجد بيانات', ha='center', va='center', transform=ax.transAxes)
                return
            
            names = [item[0][:20] + '...' if len(item[0]) > 20 else item[0] for item in top_products[:10]]
            quantities = [int(item[1]) for item in top_products[:10]]
            
            bars = ax.bar(range(len(names)), quantities)
            ax.set_title('أكثر المنتجات مبيعاً')
            ax.set_xlabel('المنتجات')
            ax.set_ylabel('الكمية المباعة')
            ax.set_xticks(range(len(names)))
            ax.set_xticklabels(names, rotation=45, ha='right')
            
            # Add value labels on bars
            for i, bar in enumerate(bars):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                       f'{quantities[i]}', ha='center', va='bottom')
            
        except Exception as e:
            ax.text(0.5, 0.5, f'خطأ في عرض البيانات: {str(e)}', ha='center', va='center', transform=ax.transAxes)
    
    def export_to_excel(self):
        """Export reports to Excel"""
        try:
            from_date = self.from_date.date().toPython()
            to_date = self.to_date.date().toPython()
            
            filename = f"reports_{from_date.strftime('%Y%m%d')}_{to_date.strftime('%Y%m%d')}.xlsx"
            
            # Get all report data
            from_datetime = datetime.combine(from_date, datetime.min.time())
            to_datetime = datetime.combine(to_date, datetime.max.time())
            
            sales_report = self.report_service.get_sales_report(from_datetime, to_datetime)
            profit_report = self.report_service.get_profit_report(from_datetime, to_datetime)
            inventory_report = self.report_service.get_inventory_report()
            top_products = self.report_service.get_top_selling_products(20, from_datetime, to_datetime)
            
            # Export to Excel
            filepath = self.excel_exporter.export_reports(
                filename, sales_report, profit_report, inventory_report, top_products
            )
            
            QMessageBox.information(self, "نجح", f"تم تصدير التقارير إلى: {filepath}")
            
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"خطأ في تصدير التقارير: {str(e)}")
