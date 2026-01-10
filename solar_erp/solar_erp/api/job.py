import frappe
from frappe import _


def get_valid_supplier(vendor, field_label):
    if not vendor:
        return None

    # Block emails
    if "@" in vendor:
        frappe.throw(
            _(f"{field_label} must be a Supplier, not an email: {vendor}")
        )

    # Must exist as Supplier
    if not frappe.db.exists("Supplier", vendor):
        frappe.throw(
            _(f"Supplier '{vendor}' does not exist. Please select a valid Supplier.")
        )

    return vendor


@frappe.whitelist()
def create_job_file_from_lead(lead_name):
    lead = frappe.get_doc("Lead", lead_name)

    # 1. Validate required fields
    if not lead.territory:
        frappe.throw(_("Territory is required"))

    if not lead.vendor_assign:
        frappe.throw(_("Technical Execution Vendor is required"))

    if not lead.meter_execution_vendor:
        frappe.throw(_("Meter Execution Vendor is required"))

    # 2. Create Job File (only one)
    job_file = frappe.get_doc({
        "doctype": "Job File",
        "lead": lead.name,
        "customer": lead.customer,
        "overall_status": "Open"
    })
    job_file.insert(ignore_permissions=True)

    # 3. Technical vendor executions
    create_execution("Technical Survey", job_file, lead, lead.vendor_assign)
    create_execution("Structure Mounting", job_file, lead, lead.vendor_assign)
    create_execution("Project Installation", job_file, lead, lead.vendor_assign)
    create_execution("Verification Handover", job_file, lead, lead.vendor_assign)

    # 4. Meter vendor executions
    create_execution("Meter Installation", job_file, lead, lead.meter_execution_vendor)
    create_execution("Meter Commissioning", job_file, lead, lead.meter_execution_vendor)

    # 5. Link back
    lead.custom_job_file = job_file.name
    lead.save(ignore_permissions=True)

    return job_file.name


def create_execution(doctype, job_file, lead, vendor, field_label="Assigned Vendor"):
    valid_vendor = get_valid_supplier(vendor, field_label)

    data = {
        "doctype": doctype,
        "job_file": job_file.name,
        "lead": lead.name,
        "status": "Draft"
    }

    if valid_vendor:
        data["assigned_vendor"] = valid_vendor

    doc = frappe.get_doc(data)
    
    # Set flags to allow setting read-only fields
    doc.flags.ignore_permissions = True
    doc.flags.ignore_validate = False
    
    doc.insert()
    
    # Ensure assigned_vendor is saved even if field is read-only
    if valid_vendor and doc.assigned_vendor != valid_vendor:
        frappe.db.set_value(doctype, doc.name, "assigned_vendor", valid_vendor, update_modified=False)
    
    frappe.db.commit()

    return doc


import frappe

def populate_execution_status(job_file, lead):
    job_file.execution_status = []

    for stage, doctype, vendor_field in [
        ("Technical Survey", "Technical Survey", "vendor_assign"),
        ("Structure Mounting", "Structure Mounting", "vendor_assign"),
        ("Project Installation", "Project Installation", "vendor_assign"),
        ("Verification & Handover", "Verification Handover", "vendor_assign"),
        ("Meter Installation", "Meter Installation", "meter_execution_vendor"),
        ("Meter Commissioning", "Meter Commissioning", "meter_execution_vendor"),
    ]:
        vendor = lead.get(vendor_field)

        job_file.append("custom_job_execution_status", {
            "stage": stage,
            "vendor": vendor,
            "status": "Draft",
            "ref_doctype": doctype,
            "ref_name": None
        })
