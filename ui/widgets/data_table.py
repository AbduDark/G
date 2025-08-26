# -*- coding: utf-8 -*-
"""
Enhanced data table widget for Al-Hussiny Mobile Shop POS System
"""

from PyQt6.QtWidgets import (QTableWidget, QTableWidgetItem, QHeaderView, 
                            QAbstractItemView, QMenu, QApplication)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont
import logging

logger = logging.getLogger(__name__)

class DataTableWidget(QTableWidget):
    """Enhanced table widget with Arabic RTL support and additional features"""
    
    # Signals
    itemDoubleClicked = pyqtSignal(object)
    itemSelectionChanged = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
        self.setup_context_menu()
    
    def setup_table(self):
        """Setup table properties"""
        # Set RTL layout
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Selection behavior
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Alternating row colors
        self.setAlternatingRowColors(True)
        
        # Grid and sorting
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        
        # Header properties
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.verticalHeader().setVisible(False)
        
        # Font settings for Arabic
        font = QFont("Tahoma", 10)
        self.setFont(font)
        
        # Style
        self.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                alternate-background-color: #f5f5f5;
                selection-background-color: #0078d4;
                selection-color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
            QHeaderView::section {
                background-color: #e9ecef;
                padding: 8px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        # Connect signals
        super().itemDoubleClicked.connect(self.itemDoubleClicked.emit)
        super().itemSelectionChanged.connect(self.itemSelectionChanged.emit)
    
    def setup_context_menu(self):
        """Setup context menu"""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def show_context_menu(self, position):
        """Show context menu"""
        if self.itemAt(position) is None:
            return
        
        menu = QMenu(self)
        
        # Copy action
        copy_action = QAction("نسخ", self)
        copy_action.triggered.connect(self.copy_selected_text)
        menu.addAction(copy_action)
        
        # Copy row action
        copy_row_action = QAction("نسخ الصف", self)
        copy_row_action.triggered.connect(self.copy_selected_row)
        menu.addAction(copy_row_action)
        
        menu.addSeparator()
        
        # Export actions
        export_action = QAction("تصدير إلى CSV", self)
        export_action.triggered.connect(self.export_to_csv)
        menu.addAction(export_action)
        
        menu.exec(self.mapToGlobal(position))
    
    def setColumns(self, headers):
        """Set table columns"""
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Auto-resize columns
        header = self.horizontalHeader()
        for i in range(len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Set last column to stretch
        if headers:
            header.setSectionResizeMode(len(headers) - 1, QHeaderView.ResizeMode.Stretch)
    
    def setData(self, data):
        """Set table data"""
        self.setRowCount(len(data))
        
        for row, row_data in enumerate(data):
            for col, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Make items read-only
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                self.setItem(row, col, item)
        
        # Auto-resize rows
        self.resizeRowsToContents()
    
    def addRow(self, row_data):
        """Add a single row"""
        row = self.rowCount()
        self.insertRow(row)
        
        for col, value in enumerate(row_data):
            if col < self.columnCount():
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.setItem(row, col, item)
    
    def updateRow(self, row, row_data):
        """Update specific row"""
        if 0 <= row < self.rowCount():
            for col, value in enumerate(row_data):
                if col < self.columnCount():
                    item = self.item(row, col)
                    if item:
                        item.setText(str(value))
                    else:
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                        self.setItem(row, col, item)
    
    def removeSelectedRows(self):
        """Remove selected rows"""
        selected_rows = self.get_selected_rows()
        for row in sorted(selected_rows, reverse=True):
            self.removeRow(row)
    
    def get_selected_rows(self):
        """Get list of selected row indices"""
        selected_rows = set()
        for item in self.selectedItems():
            selected_rows.add(item.row())
        return sorted(list(selected_rows))
    
    def get_selected_data(self):
        """Get data from selected rows"""
        selected_rows = self.get_selected_rows()
        data = []
        
        for row in selected_rows:
            row_data = []
            for col in range(self.columnCount()):
                item = self.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        
        return data
    
    def copy_selected_text(self):
        """Copy selected cell text to clipboard"""
        current_item = self.currentItem()
        if current_item:
            QApplication.clipboard().setText(current_item.text())
    
    def copy_selected_row(self):
        """Copy selected row to clipboard"""
        selected_data = self.get_selected_data()
        if selected_data:
            text = "\t".join(selected_data[0])
            QApplication.clipboard().setText(text)
    
    def export_to_csv(self):
        """Export table data to CSV"""
        from PyQt6.QtWidgets import QFileDialog
        import csv
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "تصدير إلى CSV",
                "table_data.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write headers
                    headers = []
                    for col in range(self.columnCount()):
                        headers.append(self.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Write data
                    for row in range(self.rowCount()):
                        row_data = []
                        for col in range(self.columnCount()):
                            item = self.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                logger.info(f"تم تصدير البيانات إلى: {file_path}")
                
        except Exception as e:
            logger.error(f"خطأ في تصدير البيانات: {e}")
    
    def clear_data(self):
        """Clear all table data"""
        self.setRowCount(0)
    
    def filter_data(self, filter_text, column=None):
        """Filter table data"""
        filter_text = filter_text.lower()
        
        for row in range(self.rowCount()):
            should_show = False
            
            if column is not None:
                # Filter specific column
                item = self.item(row, column)
                if item and filter_text in item.text().lower():
                    should_show = True
            else:
                # Filter all columns
                for col in range(self.columnCount()):
                    item = self.item(row, col)
                    if item and filter_text in item.text().lower():
                        should_show = True
                        break
            
            self.setRowHidden(row, not should_show)
    
    def sort_by_column(self, column, order=Qt.SortOrder.AscendingOrder):
        """Sort table by specific column"""
        self.sortItems(column, order)
    
    def set_row_color(self, row, color):
        """Set background color for specific row"""
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(color)
    
    def highlight_text(self, text, column=None):
        """Highlight specific text in table"""
        from PyQt6.QtGui import QColor
        
        highlight_color = QColor(255, 255, 0, 100)  # Yellow with transparency
        
        for row in range(self.rowCount()):
            if column is not None:
                # Highlight specific column
                item = self.item(row, column)
                if item and text.lower() in item.text().lower():
                    item.setBackground(highlight_color)
            else:
                # Highlight all columns
                for col in range(self.columnCount()):
                    item = self.item(row, col)
                    if item and text.lower() in item.text().lower():
                        item.setBackground(highlight_color)
