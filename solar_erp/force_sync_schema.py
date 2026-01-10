"""
Force sync database schema for execution doctypes to add assigned_vendor field
"""
import frappe
from frappe.model.sync import sync_for

print("\n🔧 Force Syncing Database Schema for Execution DocTypes...\n")

doctypes = [
    "Technical Survey",
    "Structure Mounting",
    "Project Installation",
    "Meter Installation",
    "Meter Commissioning",
    "Verification Handover"
]

for doctype in doctypes:
    try:
        print(f"Syncing {doctype}...")
        sync_for(doctype, force=True, reset_permissions=False)
        frappe.db.commit()
        print(f"✅ {doctype} synced successfully")
    except Exception as e:
        print(f"❌ {doctype}: Error - {str(e)}")
        frappe.db.rollback()
    print()

print("✅ Schema sync completed!\n")
