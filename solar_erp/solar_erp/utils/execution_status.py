import frappe

def sync_job_status(doc, method=None):
    if not hasattr(doc, "job_file") or not doc.job_file:
        return

    job = frappe.get_doc("Job File", doc.job_file)

    for row in job.custom_job_execution_status:
        if row.ref_doctype == doc.doctype:
            row.status = doc.status
            row.ref_name = doc.name
            break

    job.save(ignore_permissions=True)
