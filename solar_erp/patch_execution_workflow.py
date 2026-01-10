#!/usr/bin/env python3
"""
Patch execution_workflow.py to fix vendor validation
"""

import sys

file_path = "/home/ubuntu/Solar_Erp/apps/solar_erp/solar_erp/solar_erp/api/execution_workflow.py"

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Find and replace the auto_assign_vendor function
old_code = '''def auto_assign_vendor(doc, method=None):
    """
    Auto-assign vendor from previous stages to maintain continuity
    Called on before_insert for execution doctypes
    """
    if doc.get("assigned_vendor"):
        return  # Already assigned
    
    job_file = doc.get("job_file")
    if not job_file:
        return
    
    previous_vendor = get_vendor_from_previous_stages(job_file)
    if previous_vendor:
        # Double-check it's a valid User before assigning
        if frappe.db.exists("User", {"name": previous_vendor, "enabled": 1}):
            doc.assigned_vendor = previous_vendor
        else:
            frappe.logger().warning(
                f"Skipping vendor assignment: '{previous_vendor}' is not a valid User for {doc.doctype} {doc.name}"
            )'''

new_code = '''def auto_assign_vendor(doc, method=None):
    """
    Auto-assign vendor from previous stages to maintain continuity
    Called on validate for execution doctypes
    """
    # Check if vendor already assigned
    if doc.get("assigned_vendor"):
        # Validate existing vendor
        existing_vendor = doc.get("assigned_vendor")
        if not frappe.db.exists("User", {"name": existing_vendor, "enabled": 1}):
            # Invalid vendor assigned - clear it
            frappe.logger().warning(
                f"Clearing invalid vendor '{existing_vendor}' from {doc.doctype} {doc.name or 'new'}"
            )
            doc.assigned_vendor = None
        else:
            return  # Valid vendor already assigned
    
    job_file = doc.get("job_file")
    if not job_file:
        return
    
    previous_vendor = get_vendor_from_previous_stages(job_file)
    if previous_vendor:
        # Double-check it's a valid User before assigning
        if frappe.db.exists("User", {"name": previous_vendor, "enabled": 1}):
            doc.assigned_vendor = previous_vendor
        else:
            frappe.logger().warning(
                f"Skipping vendor assignment: '{previous_vendor}' is not a valid User for {doc.doctype} {doc.name or 'new'}"
            )'''

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(file_path, 'w') as f:
        f.write(content)
    print("✅ Successfully patched execution_workflow.py")
    sys.exit(0)
else:
    print("❌ Could not find target code to replace")
    print("File may have already been patched or structure changed")
    sys.exit(1)
