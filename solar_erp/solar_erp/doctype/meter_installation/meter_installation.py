# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class MeterInstallation(Document):
    def validate(self):
        """Validate the document before saving"""
        # Prevent manual creation without panel_installation link
        if self.is_new() and not self.panel_installation:
            # Allow only if created by system (ignore_permissions flag is set)
            if not self.flags.ignore_permissions:
                frappe.throw(
                    _("Meter Installation can only be created automatically when Panel Installation is approved. "
                      "Please approve the Panel Installation record first."),
                    title=_("Manual Creation Not Allowed")
                )


    def before_save(self):
        """Store previous status for comparison"""
        if not self.is_new():
            self._previous_status = frappe.db.get_value("Meter Installation", self.name, "status")
        else:
            self._previous_status = None
    
    def on_update(self):
        """Trigger auto-creation of Meter Commissioning when approved"""
        previous_status = getattr(self, '_previous_status', None)
        
        # Check if status changed to Approved
        if self.status == "Approved" and previous_status != "Approved":
            self.handle_approval()
    
    def handle_approval(self):
        """Handle Meter Installation approval - create Meter Commissioning"""
        # Create Meter Commissioning if it doesn't exist
        meter_commissioning = self.create_meter_commissioning_if_not_exists()
        
        # Link the Meter Commissioning
        if meter_commissioning:
            frappe.db.set_value("Meter Installation", self.name, "linked_meter_commissioning", meter_commissioning.name, update_modified=False)
        
        # Commit the transaction
        frappe.db.commit()
        
        # Log audit entry
        self.log_approval_audit(meter_commissioning)
    
    def create_meter_commissioning_if_not_exists(self):
        """Create Meter Commissioning record if it doesn't exist for this Job File"""
        # Check if Meter Commissioning already exists for this Job File
        existing_mc = frappe.db.exists("Meter Commissioning", {"job_file": self.job_file})
        
        if existing_mc:
            frappe.msgprint(
                _("Meter Commissioning {0} already exists for Job File {1}").format(existing_mc, self.job_file),
                alert=True
            )
            return frappe.get_doc("Meter Commissioning", existing_mc)
        
        # Create new Meter Commissioning
        meter_commissioning = frappe.get_doc({
            "doctype": "Meter Commissioning",
            "job_file": self.job_file,
            "lead": self.lead,
            "project": self.project,
            "meter_installation": self.name,
            "status": "Draft"
        })
        
        meter_commissioning.flags.ignore_permissions = True
        meter_commissioning.insert()
        
        frappe.msgprint(
            _("Meter Commissioning {0} created successfully").format(meter_commissioning.name),
            alert=True,
            indicator="green"
        )
        
        return meter_commissioning
    
    def log_approval_audit(self, meter_commissioning=None):
        """Log audit entry for Meter Installation approval"""
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Meter Installation",
            "reference_name": self.name,
            "content": _("Meter Installation approved.{0}").format(
                _(" Meter Commissioning {0} created.").format(meter_commissioning.name) if meter_commissioning else ""
            )
        }).insert(ignore_permissions=True)


@frappe.whitelist()
def start_work(docname):
    """Start work - transitions from Draft/Rework to In Progress"""
    doc = frappe.get_doc("Meter Installation", docname)
    
    if doc.status not in ["Draft", "Rework"]:
        frappe.throw(_("Can only start work when status is Draft or Rework"))
    
    # Check if user has the right role
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Meter Installation Executive"}) or
            frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Meter Installation Manager"}) or
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
    doc = frappe.get_doc("Meter Installation", docname)
    
    if doc.status != "In Progress":
        frappe.throw(_("Can only submit work when status is In Progress"))
    
    # Check if user has the right role (Executive only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Meter Installation Executive"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Meter Installation Executive can submit work for review"))
    
    doc.status = "Ready for Review"
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def hold_work(docname, reason):
    """Put work on hold - transitions to Blocked status (Executive action)"""
    doc = frappe.get_doc("Meter Installation", docname)
    
    if doc.status != "In Progress":
        frappe.throw(_("Can only hold when status is In Progress"))
    
    # Check if user has the right role
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Meter Installation Executive"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Meter Installation Executive can put work on hold"))
    
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
    doc = frappe.get_doc("Meter Installation", docname)
    
    if doc.status != "Ready for Review":
        frappe.throw(_("Can only approve when status is Ready for Review"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Meter Installation Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Meter Installation Manager can approve work"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for approval"))
    
    doc.status = "Approved"
    doc.workflow_reason = reason
    doc.reviewer = frappe.session.user
    doc.review_decision = "Approved"
    doc.review_comments = reason
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def block_work(docname, reason):
    """Block work - transitions to Blocked status (Manager action)"""
    doc = frappe.get_doc("Meter Installation", docname)
    
    if doc.status not in ["In Progress", "Ready for Review"]:
        frappe.throw(_("Can only block when status is In Progress or Ready for Review"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Meter Installation Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Meter Installation Manager can block work"))
    
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
    doc = frappe.get_doc("Meter Installation", docname)
    
    if doc.status != "Ready for Review":
        frappe.throw(_("Can only request rework when status is Ready for Review"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Meter Installation Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Meter Installation Manager can request rework"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for rework"))
    
    doc.status = "Rework"
    doc.workflow_reason = reason
    doc.reviewer = frappe.session.user
    doc.review_decision = "Rework"
    doc.review_comments = reason
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def resume_work(docname, reason):
    """Resume work - transitions from Blocked to In Progress"""
    doc = frappe.get_doc("Meter Installation", docname)
    
    if doc.status != "Blocked":
        frappe.throw(_("Can only resume when status is Blocked"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Meter Installation Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Meter Installation Manager can resume work"))
    
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
    doc = frappe.get_doc("Meter Installation", docname)
    
    if doc.status != "Approved":
        frappe.throw(_("Can only close when status is Approved"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Meter Installation Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Meter Installation Manager can close work"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for closing"))
    
    doc.status = "Closed"
    doc.workflow_reason = reason
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}
