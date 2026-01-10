"""
Custom fields for Purchase Order DocType to link back to Procurement Consolidation
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def add_purchase_order_custom_fields():
    """
    Add custom fields to Purchase Order and Purchase Order Item
    to maintain traceability to Procurement Consolidation
    """
    
    custom_fields = {
        "Purchase Order": [
            {
                "fieldname": "procurement_consolidation",
                "label": "Procurement Consolidation",
                "fieldtype": "Link",
                "options": "Procurement Consolidation",
                "insert_after": "supplier",
                "read_only": 1,
                "description": "Source Procurement Consolidation document",
                "translatable": 0
            }
        ],
        "Purchase Order Item": [
            {
                "fieldname": "source_procurement_consolidation_item",
                "label": "Source Consolidation Item",
                "fieldtype": "Data",
                "insert_after": "item_code",
                "read_only": 1,
                "hidden": 1,
                "description": "Reference to source Consolidated Procurement Item row",
                "translatable": 0
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
    
    print("✅ Purchase Order custom fields created successfully")


if __name__ == "__main__":
    add_purchase_order_custom_fields()
