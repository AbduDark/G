# -*- coding: utf-8 -*-
"""
Dashboard window for Al-Hussiny Mobile Shop POS System
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                            QLabel, QFrame, QPushButton, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont
import logging
from datetime import datetime, timedelta

from .base_window import BaseWindow
from .widgets.data_table import DataTableWidget

logger = logging.getLogger(__name__)

class DashboardWindow(BaseWindow):
    """Dashboard window with statistics and quick access"""
    
    def __init__(self, db_manager, user_data):
        super().__init__(db_manager, user_data)
        self.setup_dashboard()
        self.refresh_data()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_data)
        self.refresh_timer.start(60000)  # Refresh every minute
    
    def setup_dashboard(self):
        """Setup dashboard interface"""
        self.set_title("لوحة التحكم - محل الحسيني")
        self.setMinimumSize(1200, 800)
        
        # Main layout
        main_layout = QVBoxLayout(self.content_widget)
        main_layout.setSpacing(20)
        
        # Statistics cards
        self.setup_statistics_cards(main_layout)
        
        # Charts and tables section
        self.setup_charts_section(main_layout)
        
        # Recent activities
        self.setup_recent_activities(main_layout)
    
    def setup_statistics_cards(self, layout):
        """Setup statistics cards"""
        stats_frame = QFrame()
        stats_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        stats_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fc;
                border: 1px solid #e3e6f0;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        stats_layout = QGridLayout(stats_frame)
        stats_layout.setSpacing(15)
        
        # Initialize stats widgets
        self.stats_widgets = {}
        
        # Define statistics
        stats = [
            ("مبيعات اليوم", "0 ج.م", "#1cc88a", 0, 0),
            ("عدد الفواتير", "0", "#36b9cc", 0, 1),
            ("المنتجات المنخفضة", "0", "#f6c23e", 0, 2),
            ("الصيانات المعلقة", "0", "#e74a3b", 0, 3),
            ("إجمالي المنتجات", "0", "#5a5c69", 1, 0),
            ("العملاء", "0", "#858796", 1, 1),
            ("المبيعات الشهرية", "0 ج.م", "#4e73df", 1, 2),
            ("إجمالي الإيرادات", "0 ج.م", "#1cc88a", 1, 3)
        ]
        
        for title, value, color, row, col in stats:
            self.create_stat_card(stats_layout, title, value, color, row, col)
        
        layout.addWidget(stats_frame)
    
    def create_stat_card(self, layout, title, value, color, row, col):
        """Create individual statistics card"""
        card_frame = QFrame()
        card_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 {color}, stop: 1 {color});
                border-radius: 8px;
                color: white;
                padding: 15px;
                min-height: 100px;
            }}
        """)
        
        card_layout = QVBoxLayout(card_frame)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Value label
        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet("color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title label
        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        card_layout.addWidget(value_label)
        card_layout.addWidget(title_label)
        
        # Store reference for updates
        self.stats_widgets[title] = value_label
        
        layout.addWidget(card_frame, row, col)
    
    def setup_charts_section(self, layout):
        """Setup charts and graphs section"""
        charts_frame = QFrame()
        charts_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        charts_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e3e6f0;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        charts_layout = QHBoxLayout(charts_frame)
        
        # Sales chart placeholder
        sales_chart_frame = QFrame()
        sales_chart_frame.setFrameStyle(QFrame.Shape.Box)
        sales_chart_frame.setMinimumHeight(300)
        
        sales_chart_layout = QVBoxLayout(sales_chart_frame)
        sales_title = QLabel("مخطط المبيعات الأسبوعية")
        sales_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        sales_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Placeholder for chart
        chart_placeholder = QLabel("مخطط المبيعات\n(سيتم تنفيذه باستخدام matplotlib)")
        chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chart_placeholder.setStyleSheet("color: #858796; font-size: 14pt;")
        
        sales_chart_layout.addWidget(sales_title)
        sales_chart_layout.addWidget(chart_placeholder)
        
        # Top products table
        top_products_frame = QFrame()
        top_products_frame.setFrameStyle(QFrame.Shape.Box)
        top_products_frame.setMinimumHeight(300)
        
        top_products_layout = QVBoxLayout(top_products_frame)
        top_products_title = QLabel("أكثر المنتجات مبيعاً")
        top_products_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        top_products_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create table for top products
        self.top_products_table = DataTableWidget()
        self.top_products_table.setColumns(["المنتج", "الكمية المباعة", "الإيرادات"])
        
        top_products_layout.addWidget(top_products_title)
        top_products_layout.addWidget(self.top_products_table)
        
        charts_layout.addWidget(sales_chart_frame)
        charts_layout.addWidget(top_products_frame)
        
        layout.addWidget(charts_frame)
    
    def setup_recent_activities(self, layout):
        """Setup recent activities section"""
        activities_frame = QFrame()
        activities_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        activities_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e3e6f0;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        activities_layout = QHBoxLayout(activities_frame)
        
        # Recent sales
        recent_sales_frame = QFrame()
        recent_sales_layout = QVBoxLayout(recent_sales_frame)
        
        sales_title = QLabel("المبيعات الأخيرة")
        sales_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.recent_sales_table = DataTableWidget()
        self.recent_sales_table.setColumns(["رقم الفاتورة", "العميل", "المبلغ", "التاريخ"])
        
        recent_sales_layout.addWidget(sales_title)
        recent_sales_layout.addWidget(self.recent_sales_table)
        
        # Recent repairs
        recent_repairs_frame = QFrame()
        recent_repairs_layout = QVBoxLayout(recent_repairs_frame)
        
        repairs_title = QLabel("الصيانات الأخيرة")
        repairs_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.recent_repairs_table = DataTableWidget()
        self.recent_repairs_table.setColumns(["رقم التذكرة", "العميل", "الجهاز", "الحالة"])
        
        recent_repairs_layout.addWidget(repairs_title)
        recent_repairs_layout.addWidget(self.recent_repairs_table)
        
        activities_layout.addWidget(recent_sales_frame)
        activities_layout.addWidget(recent_repairs_frame)
        
        layout.addWidget(activities_frame)
    
    def refresh_data(self):
        """Refresh dashboard data"""
        try:
            session = self.db_manager.get_session()
            self.update_statistics(session)
            self.update_top_products(session)
            self.update_recent_activities(session)
            self.update_status("تم تحديث لوحة التحكم")
        except Exception as e:
            self.logger.error(f"خطأ في تحديث لوحة التحكم: {e}")
            self.show_message(f"خطأ في تحديث البيانات: {str(e)}", "error")
        finally:
            if 'session' in locals():
                session.close()
    
    def update_statistics(self, session):
        """Update statistics cards"""
        from models import Sale, Product, Repair, Customer
        from datetime import datetime, timedelta
        
        # Today's date range
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # This month's date range
        month_start = datetime(today.year, today.month, 1)
        
        # Today's sales
        today_sales = session.query(Sale).filter(
            Sale.created_at >= today_start,
            Sale.created_at <= today_end
        ).all()
        
        today_revenue = sum(sale.total for sale in today_sales)
        today_count = len(today_sales)
        
        # Month's sales
        month_sales = session.query(Sale).filter(
            Sale.created_at >= month_start
        ).all()
        month_revenue = sum(sale.total for sale in month_sales)
        
        # Products
        total_products = session.query(Product).filter_by(active=True).count()
        low_stock_products = session.query(Product).filter(
            Product.quantity <= Product.min_quantity,
            Product.active == True
        ).count()
        
        # Repairs
        pending_repairs = session.query(Repair).filter(
            ~Repair.status.in_(['تم التسليم', 'غير قابل للإصلاح'])
        ).count()
        
        # Customers
        total_customers = session.query(Customer).count()
        
        # Total revenue (all time)
        all_sales = session.query(Sale).all()
        total_revenue = sum(sale.total for sale in all_sales)
        
        # Update widgets
        stats_updates = {
            "مبيعات اليوم": f"{today_revenue:.2f} ج.م",
            "عدد الفواتير": str(today_count),
            "المنتجات المنخفضة": str(low_stock_products),
            "الصيانات المعلقة": str(pending_repairs),
            "إجمالي المنتجات": str(total_products),
            "العملاء": str(total_customers),
            "المبيعات الشهرية": f"{month_revenue:.2f} ج.م",
            "إجمالي الإيرادات": f"{total_revenue:.2f} ج.م"
        }
        
        for title, value in stats_updates.items():
            if title in self.stats_widgets:
                self.stats_widgets[title].setText(value)
    
    def update_top_products(self, session):
        """Update top selling products table"""
        from models import Product, SaleItem, Sale
        from sqlalchemy import func, desc
        from datetime import datetime, timedelta
        
        # Last 30 days
        date_limit = datetime.now() - timedelta(days=30)
        
        top_products = session.query(
            Product.name_ar,
            func.sum(SaleItem.quantity).label('total_sold'),
            func.sum(SaleItem.line_total).label('total_revenue')
        ).join(SaleItem).join(Sale).filter(
            Sale.created_at >= date_limit
        ).group_by(Product.id).order_by(desc('total_sold')).limit(10).all()
        
        # Update table
        data = []
        for product in top_products:
            data.append([
                product.name_ar,
                str(int(product.total_sold)),
                f"{product.total_revenue:.2f} ج.م"
            ])
        
        self.top_products_table.setData(data)
    
    def update_recent_activities(self, session):
        """Update recent activities tables"""
        from models import Sale, Repair
        from sqlalchemy import desc
        
        # Recent sales
        recent_sales = session.query(Sale).order_by(
            desc(Sale.created_at)
        ).limit(10).all()
        
        sales_data = []
        for sale in recent_sales:
            customer_name = sale.customer.name if sale.customer else "عميل نقدي"
            sales_data.append([
                sale.invoice_no,
                customer_name,
                f"{sale.total:.2f} ج.م",
                sale.created_at.strftime("%Y-%m-%d %H:%M")
            ])
        
        self.recent_sales_table.setData(sales_data)
        
        # Recent repairs
        recent_repairs = session.query(Repair).order_by(
            desc(Repair.entry_date)
        ).limit(10).all()
        
        repairs_data = []
        for repair in recent_repairs:
            customer_name = repair.customer.name if repair.customer else "غير محدد"
            repairs_data.append([
                repair.ticket_no,
                customer_name,
                repair.device_model,
                repair.status
            ])
        
        self.recent_repairs_table.setData(repairs_data)
    
    def closeEvent(self, event):
        """Handle window close"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        super().closeEvent(event)
