# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ProjectInstallation(Document):
    def validate(self):
        """Validate the document before saving"""
        # Prevent manual creation without structure_mounting link
        if self.is_new() and not self.structure_mounting:
            # Allow only if created by system (ignore_permissions flag is set)
            if not self.flags.ignore_permissions:
                frappe.throw(
                    _("Panel Installation can only be created automatically when Structure Mounting is approved. "
                      "Please approve the Structure Mounting record first."),
                    title=_("Manual Creation Not Allowed")
                )
    
    def before_save(self):
        """Store previous status for comparison"""
        if not self.is_new():
            self._previous_status = frappe.db.get_value("Panel Installation", self.name, "status")
        else:
            self._previous_status = None
    
    def on_update(self):
        """Trigger auto-creation of Meter Installation when approved"""
        previous_status = getattr(self, '_previous_status', None)
        
        # Check if status changed to Approved
        if self.status == "Approved" and previous_status != "Approved":
            self.handle_approval()
    
    def handle_approval(self):
        """Handle Panel Installation approval - create Meter Installation"""
        # Create Meter Installation if it doesn't exist
        meter_installation = self.create_meter_installation_if_not_exists()
        
        # Link the Meter Installation
        if meter_installation:
            frappe.db.set_value("Panel Installation", self.name, "linked_meter_installation", meter_installation.name, update_modified=False)
        
        # Commit the transaction
        frappe.db.commit()
        
        # Log audit entry
        self.log_approval_audit(meter_installation)
    
    def create_meter_installation_if_not_exists(self):
        """Create Meter Installation record if it doesn't exist for this Job File"""
        # Check if Meter Installation already exists for this Job File
        existing_mi = frappe.db.exists("Meter Installation", {"job_file": self.job_file})
        
        if existing_mi:
            frappe.msgprint(
                _("Meter Installation {0} already exists for Job File {1}").format(existing_mi, self.job_file),
                alert=True
            )
            return frappe.get_doc("Meter Installation", existing_mi)
        
        # Create new Meter Installation
        meter_installation = frappe.get_doc({
            "doctype": "Meter Installation",
            "job_file": self.job_file,
            "lead": self.lead,
            "project": self.project,
            "assigned_vendor": self.assigned_vendor,
            "project_installation": self.name,
            "status": "Draft"
        })
        
        meter_installation.flags.ignore_permissions = True
        meter_installation.insert()
        
        frappe.msgprint(
            _("Meter Installation {0} created successfully").format(meter_installation.name),
            alert=True,
            indicator="green"
        )
        
        return meter_installation
    
    def log_approval_audit(self, meter_installation=None):
        """Log audit entry for Panel Installation approval"""
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Panel Installation",
            "reference_name": self.name,
            "content": _("Panel Installation approved.{0}").format(
                _(" Meter Installation {0} created.").format(meter_installation.name) if meter_installation else ""
            )
        }).insert(ignore_permissions=True)


@frappe.whitelist()
def start_work(docname):
    """Start work - transitions from Draft/Rework to In Progress"""
    doc = frappe.get_doc("Panel Installation", docname)
    
    if doc.status not in ["Draft", "Rework"]:
        frappe.throw(_("Can only start work when status is Draft or Rework"))
    
    # Check if user has the right role
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Panel Installation Executive"}) or
            frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Panel Installation Manager"}) or
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
    doc = frappe.get_doc("Panel Installation", docname)
    
    if doc.status != "In Progress":
        frappe.throw(_("Can only submit work when status is In Progress"))
    
    # Check if user has the right role (Executive only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Panel Installation Executive"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Panel Installation Executive can submit work for review"))
    
    doc.status = "Ready for Review"
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}


@frappe.whitelist()
def approve_work(docname, reason):
    """Approve work - transitions from Ready for Review to Approved"""
    doc = frappe.get_doc("Panel Installation", docname)
    
    if doc.status != "Ready for Review":
        frappe.throw(_("Can only approve when status is Ready for Review"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Panel Installation Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Panel Installation Manager can approve work"))
    
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
    """Block work - transitions to Blocked status"""
    doc = frappe.get_doc("Panel Installation", docname)
    
    if doc.status not in ["In Progress", "Ready for Review"]:
        frappe.throw(_("Can only block when status is In Progress or Ready for Review"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Panel Installation Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Panel Installation Manager can block work"))
    
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
    doc = frappe.get_doc("Panel Installation", docname)
    
    if doc.status != "Ready for Review":
        frappe.throw(_("Can only request rework when status is Ready for Review"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Panel Installation Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Panel Installation Manager can request rework"))
    
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
    doc = frappe.get_doc("Panel Installation", docname)
    
    if doc.status != "Blocked":
        frappe.throw(_("Can only resume when status is Blocked"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Panel Installation Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Panel Installation Manager can resume work"))
    
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
    doc = frappe.get_doc("Panel Installation", docname)
    
    if doc.status != "Approved":
        frappe.throw(_("Can only close when status is Approved"))
    
    # Check if user has the right role (Manager only)
    if not (frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Panel Installation Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()):
        frappe.throw(_("Only Panel Installation Manager can close work"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for closing"))
    
    doc.status = "Closed"
    doc.workflow_reason = reason
    doc.save()
    frappe.db.commit()
    
    return {"status": "success"}
