"""
Wrapper script to create all execution documents with error handling

Run this script to test creating all 6 execution documents for a Job File
"""

import frappe

def test_create_all_execution_docs(job_file_name):
    """Test creating all 6 execution documents for a given Job File"""
    
    job_file = frappe.get_doc("Job File", job_file_name)
    lead = frappe.get_doc("Lead", job_file.lead)
    customer = frappe.get_doc("Customer", job_file.customer)
    
    from solar_erp.solar_erp.doc_events.lead_events import (
        create_structure_mounting_draft,
        create_project_installation_draft,
        create_meter_installation_draft,
        create_meter_commissioning_draft,
        create_verification_handover_draft
    )
    
    created = []
    failed = []
    
    # Check what already exists
    print(f"\n{'='*80}")
    print(f"Job File: {job_file_name}")
    print(f"Lead: {lead.name}")
    print(f"Customer: {customer.name}")
    print(f"{'='*80}\n")
    
    doctypes_to_create = [
        ("Structure Mounting", create_structure_mounting_draft),
        ("Project Installation", create_project_installation_draft),
        ("Meter Installation", create_meter_installation_draft),
        ("Meter Commissioning", create_meter_commissioning_draft),
        ("Verification Handover", create_verification_handover_draft),
    ]
    
    for doctype_name, create_func in doctypes_to_create:
        # Check if already exists
        existing = frappe.get_all(
            doctype_name,
            filters={"job_file": job_file_name},
            fields=["name", "status"]
        )
        
        if existing:
            print(f"✓ {doctype_name:30s} - Already exists: {existing[0].name} (Status: {existing[0].status})")
            created.append(f"{doctype_name} {existing[0].name}")
        else:
            try:
                print(f"Creating {doctype_name}...", end=" ")
                doc = create_func(job_file, lead, customer)
                frappe.db.commit()
                print(f"✅ Created: {doc.name}")
                created.append(f"{doctype_name} {doc.name}")
            except Exception as e:
                print(f"❌ FAILED: {str(e)}")
                frappe.log_error(
                    title=f"Failed to create {doctype_name} for {job_file_name}",
                    message=frappe.get_traceback()
                )
                failed.append(f"{doctype_name}: {str(e)}")
    
    print(f"\n{'='*80}")
    print(f"SUMMARY:")
    print(f"{'='*80}")
    print(f"✅ Created/Existing: {len(created)}")
    for doc in created:
        print(f"  - {doc}")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}")
        for doc in failed:
            print(f"  - {doc}")
    
    print(f"{'='*80}\n")
    
    return created, failed

if __name__ == "__main__":
    # Get the most recent Job File
    recent_jobs = frappe.get_all(
        "Job File",
        fields=["name"],
        order_by="creation desc",
        limit=1
    )
    
    if recent_jobs:
        job_file_name = recent_jobs[0].name
        create, failed = test_create_all_execution_docs(job_file_name)
    else:
        print("No Job Files found!")
