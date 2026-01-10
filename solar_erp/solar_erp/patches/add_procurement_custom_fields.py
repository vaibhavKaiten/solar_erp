# Copyright (c) 2025, KaitenSoftware
# Script to add procurement-related custom fields for auto Material Request feature

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Add custom fields for procurement workflow"""
    
    print("Adding procurement custom fields...")
    
    # Custom fields for Sales Order
    sales_order_fields = [
        {
            "fieldname": "custom_procurement_status",
            "fieldtype": "Select",
            "label": "Procurement Status",
            "options": "\nConfirmed\nPending Procurement\nReady for Delivery",
            "insert_after": "delivery_status",
            "read_only": 1,
            "in_list_view": 0,
            "in_standard_filter": 1,
            "allow_on_submit": 1,
            "translatable": 0
        },
        {
            "fieldname": "custom_linked_material_request",
            "fieldtype": "Link",
            "label": "Linked Material Request",
            "options": "Material Request",
            "insert_after": "custom_procurement_status",
            "read_only": 1,
            "allow_on_submit": 1
        },
        {
            "fieldname": "custom_stock_reserved",
            "fieldtype": "Check",
            "label": "Stock Reserved",
            "insert_after": "custom_linked_material_request",
            "read_only": 1,
            "default": "0",
            "allow_on_submit": 1
        },
        {
            "fieldname": "custom_reservation_timestamp",
            "fieldtype": "Datetime",
            "label": "Reservation Timestamp",
            "insert_after": "custom_stock_reserved",
            "read_only": 1,
            "allow_on_submit": 1
        },
    ]
    
    # Custom fields for Material Request
    material_request_fields = [
        {
            "fieldname": "custom_auto_generated",
            "fieldtype": "Check",
            "label": "Auto Generated",
            "insert_after": "material_request_type",
            "read_only": 1,
            "default": "0",
            "description": "Automatically created from Sales Order shortage"
        },
        {
            "fieldname": "custom_source_sales_order",
            "fieldtype": "Link",
            "label": "Source Sales Order",
            "options": "Sales Order",
            "insert_after": "custom_auto_generated",
            "read_only": 1
        },
        {
            "fieldname": "custom_source_technical_survey",
            "fieldtype": "Link",
            "label": "Source Technical Survey",
            "options": "Technical Survey",
            "insert_after": "custom_source_sales_order",
            "read_only": 1
        },
        {
            "fieldname": "custom_source_customer",
            "fieldtype": "Link",
            "label": "Source Customer",
            "options": "Customer",
            "insert_after": "custom_source_technical_survey",
            "read_only": 1
        },
    ]
    
    # Create Sales Order fields
    for field in sales_order_fields:
        field_name = f"Sales Order-{field['fieldname']}"
        if not frappe.db.exists("Custom Field", field_name):
            cf = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Sales Order",
                **field
            })
            cf.insert(ignore_permissions=True)
            print(f"Created: {field_name}")
        else:
            # Update existing field
            cf = frappe.get_doc("Custom Field", field_name)
            for key, value in field.items():
                setattr(cf, key, value)
            cf.save(ignore_permissions=True)
            print(f"Updated: {field_name}")
    
    # Create Material Request fields
    for field in material_request_fields:
        field_name = f"Material Request-{field['fieldname']}"
        if not frappe.db.exists("Custom Field", field_name):
            cf = frappe.get_doc({
                "doctype": "Custom Field",
                "dt": "Material Request",
                **field
            })
            cf.insert(ignore_permissions=True)
            print(f"Created: {field_name}")
        else:
            # Update existing field
            cf = frappe.get_doc("Custom Field", field_name)
            for key, value in field.items():
                setattr(cf, key, value)
            cf.save(ignore_permissions=True)
            print(f"Updated: {field_name}")
    
    frappe.db.commit()
    print("Procurement custom fields added successfully!")


if __name__ == "__main__":
    execute()
