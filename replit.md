# Al-Hussiny Mobile Shop POS System

## Overview

The Al-Hussiny Mobile Shop POS System is a comprehensive desktop application built with Python and PyQt6, designed for managing a mobile phone accessories shop. The system provides complete functionality for inventory management, sales processing, repair services, financial transfers, user management, and reporting. The application features a fully Arabic interface with RTL (right-to-left) layout support and uses SQLite as its local database solution.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Desktop Application Framework**: PyQt6-based windowing system with Arabic RTL support
- **Multi-Window Design**: Each major function operates in independent windows rather than a single tabbed interface
- **Component Structure**: Modular UI components with separate windows for inventory, sales, repairs, transfers, reports, and user management
- **Styling System**: Centralized theming with light/dark mode support using QSS stylesheets
- **Arabic Localization**: Full Arabic interface with proper font handling for Arabic text display

### Backend Architecture
- **Service Layer Pattern**: Business logic separated into dedicated service classes (AuthService, InventoryService, SalesService, etc.)
- **Repository Pattern**: Database operations abstracted through service layer with proper session management
- **Blueprint Structure**: Flask-style route organization with separate modules for different functional areas
- **Authentication & Authorization**: Role-based permission system with decorators for access control

### Data Storage Solutions
- **Primary Database**: SQLite local database stored in user's AppData directory
- **Database Models**: SQLAlchemy ORM with comprehensive model relationships
- **Schema Management**: Automatic database initialization with default data seeding
- **Data Backup**: Automated backup system with configurable retention policies

### Authentication and Authorization
- **Password Security**: bcrypt-based password hashing for user authentication
- **Session Management**: User session tracking with login/logout audit trails
- **Role-Based Access**: Hierarchical role system (Admin, Manager, Cashier, Technician, Viewer)
- **Permission Granularity**: Fine-grained permissions for different system operations

### Core Business Modules
- **Inventory Management**: Product catalog with categories, suppliers, stock tracking, and low-stock alerts
- **Sales Processing**: Invoice generation, cart management, payment processing, and receipt printing
- **Repair Services**: Ticket-based repair tracking with status management and cost calculation
- **Financial Transfers**: Balance transfer tracking for mobile money services (Vodafone Cash, etc.)
- **Reporting & Analytics**: Sales reports, profit analysis, inventory reports with Excel export capabilities

### File Organization
- **Configuration Management**: Centralized configuration with shop settings and user preferences
- **Logging System**: Comprehensive logging with file-based log rotation
- **PDF Generation**: Invoice and report PDF generation using ReportLab with Arabic support
- **Excel Export**: Report data export to Excel format with Arabic text support
- **Backup Management**: Database backup and restore functionality with compression

## External Dependencies

### Core Framework Dependencies
- **PyQt6**: Primary GUI framework for desktop application interface
- **SQLAlchemy**: ORM framework for database operations and model management
- **Flask**: Web framework components used for route organization and session management
- **bcrypt**: Password hashing library for secure user authentication

### Database & Storage
- **SQLite**: Local database engine for data persistence
- **sqlite3**: Python SQLite interface for direct database operations

### Document Generation
- **ReportLab**: PDF generation library for invoices and reports
- **openpyxl**: Excel file generation and manipulation for report exports
- **pandas**: Data manipulation and analysis for report processing

### UI & Styling
- **matplotlib**: Chart and graph generation for analytics dashboard
- **Noto Sans Arabic**: Arabic font support for proper text rendering

### Utility Libraries
- **pathlib**: Modern file path handling across different operating systems
- **datetime**: Date and time operations for business logic and reporting
- **json**: Configuration and data serialization for settings management
- **zipfile**: Backup compression and archive management
- **shutil**: File operations for backup and restore functionality

### Development & Deployment
- **logging**: Application logging and error tracking
- **configparser**: Configuration file management for application settings
- **sys/os**: System integration for file paths and environment management