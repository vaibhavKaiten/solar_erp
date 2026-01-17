"""
Script to make territory field mandatory on Lead DocType
Run this using: bench --site rgespdev.koristu.app execute solar_erp.solar_erp.make_territory_mandatory.execute
"""
import frappe

def execute():
    """Create Property Setter to make territory mandatory on Lead"""
    
    # Check if Property Setter already exists
    existing = frappe.db.exists("Property Setter", {
        "doc_type": "Lead",
        "field_name": "territory",
        "property": "reqd"
    })
    
    if existing:
        frappe.db.set_value("Property Setter", existing, "value", "1")
        print(f"Updated existing Property Setter: {existing}")
    else:
        # Create new Property Setter
        ps = frappe.get_doc({
            "doctype": "Property Setter",
            "doctype_or_field": "DocField",
            "doc_type": "Lead",
            "field_name": "territory",
            "property": "reqd",
            "property_type": "Check",
            "value": "1",
            "module": "Solar Project"
        })
        ps.insert(ignore_permissions=True)
        print(f"Created Property Setter: {ps.name}")
    
    frappe.db.commit()
    print("Territory field is now mandatory on Lead!")

if __name__ == "__main__":
    execute()
