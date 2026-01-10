# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class VerificationHandover(Document):
    def validate(self):
        """Validate the document before saving"""
        # Prevent manual creation without meter_commissioning link
        if self.is_new() and not self.meter_commissioning:
            # Allow only if created by system (ignore_permissions flag is set)
            if not self.flags.ignore_permissions:
                frappe.throw(
                    _("Verification Handover can only be created automatically when Meter Commissioning is approved. "
                      "Please approve the Meter Commissioning record first."),
                    title=_("Manual Creation Not Allowed")
                )


@frappe.whitelist()
def start_work(docname):
    """Start work - transitions from Draft/Rework to In Progress"""
    doc = frappe.get_doc("Verification Handover", docname)
    
    if doc.status not in ["Draft", "Rework"]:
        frappe.throw(_("Can only start work when status is Draft or Rework"))
    
    # Check if user has the right role
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Verification Handover Executive"}) or
            frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Verification Handover Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("You don't have permission to start this work"))
    
    doc.status = "In Progress"
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def submit_work(docname):
    """Submit work for review - transitions from In Progress to Ready for Review"""
    doc = frappe.get_doc("Verification Handover", docname)
    
    if doc.status != "In Progress":
        frappe.throw(_("Can only submit work when status is In Progress"))
    
    # Check if user has the right role (Executive only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Verification Handover Executive"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Verification Handover Executive can submit work for review"))
    
    doc.status = "Ready for Review"
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def hold_work(docname, reason):
    """Put work on hold - transitions to Blocked status (Executive action)"""
    doc = frappe.get_doc("Verification Handover", docname)
    
    if doc.status != "In Progress":
        frappe.throw(_("Can only hold when status is In Progress"))
    
    # Check if user has the right role
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Verification Handover Executive"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Verification Handover Executive can put work on hold"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for putting on hold"))
    
    doc.status = "Blocked"
    doc.workflow_reason = reason
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def approve_work(docname, reason):
    """Approve work - transitions from Ready for Review to Approved"""
    doc = frappe.get_doc("Verification Handover", docname)
    
    if doc.status != "Ready for Review":
        frappe.throw(_("Can only approve when status is Ready for Review"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Verification Handover Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Verification Handover Manager can approve work"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for approval"))
    
    doc.status = "Approved"
    doc.workflow_reason = reason
    doc.reviewer = frappe.session.user
    doc.review_decision = "Approved"
    doc.closure_comments = reason
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def block_work(docname, reason):
    """Block work - transitions to Blocked status (Manager action)"""
    doc = frappe.get_doc("Verification Handover", docname)
    
    if doc.status not in ["In Progress", "Ready for Review"]:
        frappe.throw(_("Can only block when status is In Progress or Ready for Review"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Verification Handover Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Verification Handover Manager can block work"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for blocking"))
    
    doc.status = "Blocked"
    doc.workflow_reason = reason
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def request_rework(docname, reason):
    """Request rework - transitions from Ready for Review to Rework"""
    doc = frappe.get_doc("Verification Handover", docname)
    
    if doc.status != "Ready for Review":
        frappe.throw(_("Can only request rework when status is Ready for Review"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Verification Handover Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Verification Handover Manager can request rework"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for rework"))
    
    doc.status = "Rework"
    doc.workflow_reason = reason
    doc.reviewer = frappe.session.user
    doc.review_decision = "Rework"
    doc.closure_comments = reason
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def resume_work(docname, reason):
    """Resume work - transitions from Blocked to In Progress"""
    doc = frappe.get_doc("Verification Handover", docname)
    
    if doc.status != "Blocked":
        frappe.throw(_("Can only resume when status is Blocked"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Verification Handover Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Verification Handover Manager can resume work"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for resuming"))
    
    doc.status = "In Progress"
    doc.workflow_reason = reason
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def close_work(docname, reason):
    """Close work - transitions from Approved to Closed"""
    doc = frappe.get_doc("Verification Handover", docname)
    
    if doc.status != "Approved":
        frappe.throw(_("Can only close when status is Approved"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Verification Handover Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Verification Handover Manager can close work"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for closing"))
    
    doc.status = "Closed"
    doc.workflow_reason = reason
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}
