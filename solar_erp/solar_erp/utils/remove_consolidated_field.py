#!/usr/bin/env python3
# Copyright (c) 2026, Kaiten Software and contributors
# For license information, please see license.txt

"""
Script to remove the 'consolidated_for_planning' custom field from Material Request
"""

import frappe

def remove_consolidated_field():
    """
    Remove the consolidated_for_planning custom field from Material Request DocType
    """
    try:
        # Check if the custom field exists
        custom_field_name = frappe.db.get_value(
            "Custom Field",
            {
                "dt": "Material Request",
                "fieldname": "consolidated_for_planning"
            },
            "name"
        )
        
        if custom_field_name:
            print(f"Found custom field: {custom_field_name}")
            
            # Delete the custom field
            frappe.delete_doc("Custom Field", custom_field_name, force=1)
            frappe.db.commit()
            
            print(f"✓ Successfully deleted custom field 'consolidated_for_planning' from Material Request")
        else:
            print("⚠ Custom field 'consolidated_for_planning' not found in Material Request")
        
        # Clear cache to ensure changes take effect
        frappe.clear_cache(doctype="Material Request")
        print("✓ Cache cleared for Material Request DocType")
        
    except Exception as e:
        print(f"✗ Error removing custom field: {str(e)}")
        frappe.db.rollback()
        raise


if __name__ == "__main__":
    remove_consolidated_field()
