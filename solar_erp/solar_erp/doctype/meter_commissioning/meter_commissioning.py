# meter_commissioning.py (REFINED – Workflow-driven)
# Single source of truth: workflow_state
# ZERO manual status mutations
# ALL role + transition logic lives in Workflow

import frappe
from frappe import _
from frappe.model.document import Document


class MeterCommissioning(Document):
    def validate(self):
        self.validate_creation_source()
        self.validate_vendor_requirement()

    def on_update(self):
        """React ONLY to workflow transitions."""
        if self.workflow_state == "Approved":
            self.handle_approval()

    # ------------------------------------------------------------------
    # VALIDATIONS
    # ------------------------------------------------------------------
    def validate_creation_source(self):
        """Prevent manual creation unless system-generated."""
        if self.is_new() and not self.meter_installation:
            if not self.flags.ignore_permissions:
                frappe.throw(
                    _("Meter Commissioning can only be created automatically from Meter Installation approval."),
                    title=_('Manual Creation Not Allowed')
                )

    def validate_vendor_requirement(self):
        if self.workflow_state != "Draft" and not self.assigned_vendor:
            frappe.throw(_("Assigned Vendor is mandatory before proceeding."))

    # ------------------------------------------------------------------
    # APPROVAL HANDLING
    # ------------------------------------------------------------------
    def handle_approval(self):
        """Executed once when Meter Commissioning is Approved."""
        # Idempotency guard
        if self.linked_verification_handover:
            return

        verification_handover = self.create_verification_handover_if_missing()

        if verification_handover:
            frappe.db.set_value(
                "Meter Commissioning",
                self.name,
                "linked_verification_handover",
                verification_handover.name,
                update_modified=False
            )

        frappe.db.commit()
        self.log_approval(verification_handover)

    def create_verification_handover_if_missing(self):
        existing = frappe.db.exists(
            "Verification Handover",
            {"job_file": self.job_file}
        )

        if existing:
            return frappe.get_doc("Verification Handover", existing)

        doc = frappe.get_doc({
            "doctype": "Verification Handover",
            "job_file": self.job_file,
            "lead": self.lead,
            "project": self.project,
            "meter_commissioning": self.name,
            "assigned_vendor": self.assigned_vendor,
            "workflow_state": "Draft"
        })

        doc.flags.ignore_permissions = True
        doc.insert()

        frappe.msgprint(
            _(f"Verification Handover {doc.name} created"),
            indicator="green",
            alert=True
        )

        return doc

    def log_approval(self, verification_handover=None):
        message = "Meter Commissioning approved."
        if verification_handover:
            message += f" Verification Handover {verification_handover.name} created."

        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Meter Commissioning",
            "reference_name": self.name,
            "content": _(message)
        }).insert(ignore_permissions=True)


# ----------------------------------------------------------------------
# DELETE / IGNORE ALL OLD IMPLEMENTATION CODE:
# - before_save with _previous_status
# - ALL @frappe.whitelist() APIs (start_work, approve_work, etc.)
# - status field mutations
# - role checks in Python
#
# Workflow handles:
# - State transitions
# - Role permissions
# - Reasons / conditions
# ----------------------------------------------------------------------
