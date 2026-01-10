"""
Manual Job File Creation Test - Bypass vendor issues
"""
import frappe

def create_job_file_without_vendor():
    """
    Get most recent Qualified Lead and try to create Job File manually without vendor
    """
    print("\n" + "="*80)
    print("MANUAL JOB FILE CREATION TEST")
    print("="*80 + "\n")
    
    # Get the most recent Qualified Lead without a Job File
    leads = frappe.get_all(
        "Lead",
        filters={
            "status": "Qualified",
            "custom_job_file": ["is", "not set"]
        },
        fields=["name", "lead_name", "assign_vendor", "company_name", "first_name", "last_name"],
        order_by="modified desc",
        limit=1
    )
    
    if not leads:
        print("❌ No Qualified Leads without Job File found")
        return
    
    lead_data = leads[0]
    lead = frappe.get_doc("Lead", lead_data.name)
    
    print(f"Lead: {lead.name} ({lead.lead_name})")
    print(f"Assigned Vendor: {lead.assign_vendor or 'None'}")
    
    # FORCE CLEAR the vendor
    print("\n✅ Forcefully clearing assign_vendor...")
    frappe.db.set_value("Lead", lead.name, "assign_vendor", None, update_modified=False)
    frappe.db.commit()
    lead.reload()
    
    print(f"Vendor after clearing: {lead.assign_vendor or 'None'}")
    
    # Now call the creation function
    print("\n▶️  Attempting to create Job File...")
    
    try:
        from solar_erp.solar_erp.doc_events.lead_events import create_job_file_from_lead
        create_job_file_from_lead(lead)
        print("\n✅ SUCCESS! Job File created")
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    create_job_file_without_vendor()
