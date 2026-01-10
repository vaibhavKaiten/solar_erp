# Copyright (c) 2025, Solar ERP
# Script to create custom fields for Sales Order

import frappe

def execute():
    """Create custom fields for Sales Order BOM integration"""
    
    fields = [
        {
            "doctype": "Custom Field",
            "dt": "Sales Order",
            "fieldname": "custom_bom_section",
            "fieldtype": "Section Break",
            "label": "Approved BOM Components",
            "insert_after": "terms",
            "collapsible": 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales Order",
            "fieldname": "custom_technical_survey",
            "fieldtype": "Link",
            "label": "Technical Survey",
            "options": "Technical Survey",
            "insert_after": "custom_bom_section",
            "read_only": 1
        },
        {
            "doctype": "Custom Field",
            "dt": "Sales Order",
            "fieldname": "custom_bom_items",
            "fieldtype": "Table",
            "label": "BOM Items",
            "options": "Sales Order BOM Item",
            "insert_after": "custom_technical_survey",
            "read_only": 1
        }
    ]
    
    for f in fields:
        if not frappe.db.exists("Custom Field", f["dt"] + "-" + f["fieldname"]):
            frappe.get_doc(f).insert()
            print(f"Created {f['fieldname']}")
        else:
            print(f"Already exists: {f['fieldname']}")
    
    frappe.db.commit()
    print("Done!")


if __name__ == "__main__":
    execute()
