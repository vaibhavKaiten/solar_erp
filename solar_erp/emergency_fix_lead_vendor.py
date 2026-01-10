"""
Emergency script to find and clear invalid vendor from Lead
"""
import frappe

def fix_lead_vendor():
    """Find all Leads with invalid vendors and clear them"""
    
    print("\n" + "="*80)
    print("EMERGENCY: Finding and Fixing Invalid Vendors on Leads")
    print("="*80 + "\n")
    
    # Get all Leads with assign_vendor set
    leads = frappe.get_all(
        "Lead",
        filters={"assign_vendor": ["is", "set"]},
        fields=["name", "assign_vendor", "lead_name", "custom_job_file"],
        order_by="modified desc",
        limit=20
    )
    
    print(f"Found {len(leads)} Leads with assign_vendor set\n")
    
    fixed_count = 0
    valid_count = 0
    
    for lead in leads:
        vendor_email = lead.assign_vendor
        
        # Check if vendor exists as User
        vendor_exists = frappe.db.exists("User", {"name": vendor_email, "enabled": 1})
        
        if not vendor_exists:
            print(f"❌ Lead: {lead.name} ({lead.lead_name})")
            print(f"   Invalid Vendor: {vendor_email}")
            print(f"   Job File: {lead.custom_job_file or 'None'}")
            
            # Clear the vendor
            try:
                frappe.db.set_value("Lead", lead.name, "assign_vendor", None, update_modified=False)
                frappe.db.commit()
                print(f"   ✅ CLEARED invalid vendor\n")
                fixed_count += 1
            except Exception as e:
                print(f"   ⚠️ Error clearing: {str(e)}\n")
        else:
            print(f"✅ Lead: {lead.name} - Vendor OK: {vendor_email}")
            valid_count += 1
    
    print("\n" + "="*80)
    print("SUMMARY:")
    print("="*80)
    print(f"✅ Valid vendors: {valid_count}")
    print(f"❌ Invalid vendors cleared: {fixed_count}")
    print("="*80 + "\n")
    
    if fixed_count > 0:
        print("✅ Fixed! Try 'Initiate Job Case' again now.")
    else:
        print("ℹ️  No invalid vendors found on Leads.")
        print("   The error might be coming from elsewhere.")
    
    return fixed_count

if __name__ == "__main__":
    fix_lead_vendor()
