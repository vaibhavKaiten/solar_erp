# Copyright (c) 2025, Solar ERP
# Script to add custom_sales_order field to Quotation

import frappe

def execute():
    """Add custom_sales_order field to Quotation"""
    
    if not frappe.db.exists("Custom Field", "Quotation-custom_sales_order"):
        frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "Quotation",
            "fieldname": "custom_sales_order",
            "fieldtype": "Link",
            "options": "Sales Order",
            "label": "Linked Sales Order",
            "insert_after": "custom_quotation_status",
            "read_only": 1
        }).insert()
        print("Created custom_sales_order field")
    else:
        print("Field already exists")
    
    frappe.db.commit()


if __name__ == "__main__":
    execute()
