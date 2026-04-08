"""
API Routers

Contains all FastAPI routers for different endpoints:
- invoices: Invoice upload and management
- negotiations: Vendor negotiation operations
- factories: Factory management and dashboard
- vendors: Vendor registration and search
- admin: Admin and monitoring endpoints
"""

from app.api import invoices, negotiations, factories, vendors, admin

__all__ = ["invoices", "negotiations", "factories", "vendors", "admin"]
