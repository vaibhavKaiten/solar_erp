"""
Add assigned_vendor field to execution DocTypes if missing
Run with: bench --site rgespdev.koristu.app console < fix_assigned_vendor_fields.py
"""

import frappe

print("\n" + "="*80)
print("🔧 Adding assigned_vendor field to execution DocTypes")
print("="*80 + "\n")

# List of execution DocTypes that need the assigned_vendor field
doctypes = [
    "Technical Survey",
    "Structure Mounting",
    "Panel Installation",  # This is "Project Installation" in code but might be "Panel Installation" in DB
    "Project Installation",
    "Meter Installation",
    "Meter Commissioning",
    "Verification Handover"
]

for doctype in doctypes:
    try:
        # Check if DocType exists
        if not frappe.db.exists("DocType", doctype):
            print(f"⚠️  DocType '{doctype}' does not exist - skipping")
            continue
        
        # Get the DocType
        doc = frappe.get_doc("DocType", doctype)
        
        # Check if assigned_vendor field already exists
        existing_field = None
        for field in doc.fields:
            if field.fieldname == "assigned_vendor":
                existing_field = field
                break
        
        if existing_field:
            print(f"✅ {doctype}: assigned_vendor field already exists")
            # Make sure it's a Link to Supplier
            if existing_field.fieldtype != "Link" or existing_field.options != "Supplier":
                print(f"   ⚠️  Fixing field type: {existing_field.fieldtype} → Link (Supplier)")
                existing_field.fieldtype = "Link"
                existing_field.options = "Supplier"
                doc.save()
        else:
            print(f"➕ {doctype}: Adding assigned_vendor field")
            # Add the field
            doc.append("fields", {
                "fieldname": "assigned_vendor",
                "fieldtype": "Link",
                "label": "Assigned Vendor",
                "options": "Supplier",
                "insert_after": "job_file"
            })
            doc.save()
        
    except Exception as e:
        print(f"❌ Error with {doctype}: {str(e)}")

print()
print("="*80)
print("✅ Field updates complete - now run: bench --site rgespdev.koristu.app migrate")
print("="*80)
print()
