"""
Disable the Client Script that adds 'Create Job File' button
Run this with: bench --site rgespdev.koristu.app console < disable_create_job_button.py
"""

import frappe

print("\n" + "="*80)
print("🔧 Disabling 'Create Job File' button Client Script...")
print("="*80 + "\n")

script_name = "Auto-create Job File when Lead is 'Initiate Job'"

try:
    # Check if script exists
    if frappe.db.exists("Client Script", script_name):
        # Disable the script
        frappe.db.set_value("Client Script", script_name, "enabled", 0)
        frappe.db.commit()
        print(f"✅ Successfully disabled Client Script: '{script_name}'")
        print(f"   The 'Create Job File' button will no longer appear on Lead forms")
    else:
        print(f"⚠️  Client Script '{script_name}' not found")
except Exception as e:
    print(f"❌ Error: {str(e)}")
    frappe.db.rollback()

print("\n" + "="*80)
print("✅ DONE - Please clear cache with: bench --site rgespdev.koristu.app clear-cache")
print("="*80 + "\n")
