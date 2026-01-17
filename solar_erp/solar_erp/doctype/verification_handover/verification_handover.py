# verification_handover.py (REFINED – Workflow-driven)
# Single source of truth: workflow_state
# ZERO manual status mutations
# ALL transitions + roles handled by Workflow

import frappe
from frappe import _
from frappe.model.document import Document


class VerificationHandover(Document):
    def validate(self):
        self.validate_creation_source()
        self.validate_vendor_requirement()

    def on_update(self):
        """React only to workflow transitions."""
        if self.workflow_state == "Approved":
            self.handle_approval()

    # ------------------------------------------------------------------
    # VALIDATIONS
    # ------------------------------------------------------------------
    def validate_creation_source(self):
        """Prevent manual creation unless system-generated."""
        if self.is_new() and not self.meter_commissioning:
            if not self.flags.ignore_permissions:
                frappe.throw(
                    _("Verification Handover can only be created automatically from Meter Commissioning approval."),
                    title=_('Manual Creation Not Allowed')
                )

    def validate_vendor_requirement(self):
        if self.workflow_state != "Draft" and not self.assigned_vendor:
            frappe.throw(_("Assigned Vendor is mandatory before proceeding."))

    # ------------------------------------------------------------------
    # APPROVAL HANDLING
    # ------------------------------------------------------------------
    def handle_approval(self):
        """Executed once when Verification Handover is Approved."""
        # Idempotency guard
        if self.handover_completed:
            return

        # Mark handover as completed
        frappe.db.set_value(
            "Verification Handover",
            self.name,
            "handover_completed",
            1,
            update_modified=False
        )

        frappe.db.commit()
        self.log_approval()

    def log_approval(self):
        message = "Verification Handover approved and completed."

        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Verification Handover",
            "reference_name": self.name,
            "content": _(message)
        }).insert(ignore_permissions=True)


# ----------------------------------------------------------------------
# DELETE / IGNORE ALL OLD IMPLEMENTATION CODE:
# - ALL @frappe.whitelist() APIs (start_work, submit_work, approve_work, etc.)
# - status field mutations
# - workflow_state assignments in Python
# - role checks in Python
#
# Workflow MUST handle:
# - Assigned to Vendor
# - In Progress
# - Ready for Review
# - Rework / Blocked
# - Approved
# - Closed
# ----------------------------------------------------------------------
