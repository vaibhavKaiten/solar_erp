# meter_installation.py (REFINED – Workflow-driven)
# Single source of truth: workflow_state
# NO manual status mutations
# NO whitelisted state-transition APIs

import frappe
from frappe import _
from frappe.model.document import Document


class MeterInstallation(Document):
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
        if self.is_new() and not self.project_installation:
            if not self.flags.ignore_permissions:
                frappe.throw(
                    _("Meter Installation can only be created automatically from Project Installation approval."),
                    title=_('Manual Creation Not Allowed')
                )

    def validate_vendor_requirement(self):
        if self.workflow_state != "Draft" and not self.assigned_vendor:
            frappe.throw(_("Assigned Vendor is mandatory before proceeding."))

    # ------------------------------------------------------------------
    # APPROVAL HANDLING
    # ------------------------------------------------------------------
    def handle_approval(self):
        """Executed once when Meter Installation is Approved."""
        # Idempotency guard
        if self.linked_meter_commissioning:
            return

        meter_commissioning = self.create_meter_commissioning_if_missing()

        if meter_commissioning:
            frappe.db.set_value(
                "Meter Installation",
                self.name,
                "linked_meter_commissioning",
                meter_commissioning.name,
                update_modified=False
            )

        frappe.db.commit()
        self.log_approval(meter_commissioning)

    def create_meter_commissioning_if_missing(self):
        existing = frappe.db.exists(
            "Meter Commissioning",
            {"job_file": self.job_file}
        )

        if existing:
            return frappe.get_doc("Meter Commissioning", existing)

        doc = frappe.get_doc({
            "doctype": "Meter Commissioning",
            "job_file": self.job_file,
            "lead": self.lead,
            "project": self.project,
            "meter_installation": self.name,
            "assigned_vendor": self.assigned_vendor,
            "workflow_state": "Draft"
        })

        doc.flags.ignore_permissions = True
        doc.insert()

        frappe.msgprint(
            _(f"Meter Commissioning {doc.name} created"),
            indicator="green",
            alert=True
        )

        return doc

    def log_approval(self, meter_commissioning=None):
        message = "Meter Installation approved."
        if meter_commissioning:
            message += f" Meter Commissioning {meter_commissioning.name} created."

        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Meter Installation",
            "reference_name": self.name,
            "content": _(message)
        }).insert(ignore_permissions=True)


# ----------------------------------------------------------------------
# ALL STATE TRANSITIONS ARE HANDLED BY WORKFLOW
# Delete / ignore ALL whitelisted methods from old implementation:
# start_work, submit_work, hold_work, approve_work, block_work,
# request_rework, resume_work, close_work, initiate_meter_installation
# ----------------------------------------------------------------------
