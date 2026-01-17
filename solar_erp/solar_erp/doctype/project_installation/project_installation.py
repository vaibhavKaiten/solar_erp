# project_installation.py (REFINED – Workflow-driven)
# Single source of truth: workflow_state
# NO manual status transitions, NO whitelisted state APIs

import frappe
from frappe import _
from frappe.model.document import Document


class ProjectInstallation(Document):
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
        if self.is_new() and not self.structure_mounting:
            if not self.flags.ignore_permissions:
                frappe.throw(
                    _("Project Installation can only be created automatically from Structure Mounting approval."),
                    title=_('Manual Creation Not Allowed')
                )

    def validate_vendor_requirement(self):
        if self.workflow_state != 'Draft' and not self.assigned_vendor:
            frappe.throw(_("Assigned Vendor is mandatory before proceeding."))

    # ------------------------------------------------------------------
    # APPROVAL HANDLING
    # ------------------------------------------------------------------
    def handle_approval(self):
        """Executed once when Project Installation is Approved."""
        # Idempotency guard
        if self.linked_meter_installation:
            return

        meter_installation = self.create_meter_installation_if_missing()

        if meter_installation:
            frappe.db.set_value(
                "Project Installation",
                self.name,
                "linked_meter_installation",
                meter_installation.name,
                update_modified=False
            )

        frappe.db.commit()
        self.log_approval(meter_installation)

    def create_meter_installation_if_missing(self):
        existing = frappe.db.exists(
            "Meter Installation",
            {"job_file": self.job_file}
        )

        if existing:
            return frappe.get_doc("Meter Installation", existing)

        doc = frappe.get_doc({
            "doctype": "Meter Installation",
            "job_file": self.job_file,
            "lead": self.lead,
            "project": self.project,
            "assigned_vendor": self.assigned_vendor,
            "project_installation": self.name,
            "workflow_state": "Draft"
        })

        doc.flags.ignore_permissions = True
        doc.insert()

        frappe.msgprint(
            _(f"Meter Installation {doc.name} created"),
            indicator="green",
            alert=True
        )

        return doc

    def log_approval(self, meter_installation=None):
        message = "Project Installation approved."
        if meter_installation:
            message += f" Meter Installation {meter_installation.name} created."

        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Project Installation",
            "reference_name": self.name,
            "content": _(message)
        }).insert(ignore_permissions=True)


# ----------------------------------------------------------------------
# ALL STATE TRANSITIONS ARE HANDLED BY WORKFLOW
# No start / submit / approve / rework / block / resume / close APIs
# ----------------------------------------------------------------------
