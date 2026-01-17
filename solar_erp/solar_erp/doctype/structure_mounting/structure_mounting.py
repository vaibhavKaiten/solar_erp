# structure_mounting.py (REFINED – Workflow-driven)
# Single source of truth: workflow_state
# NO manual status mutations

import frappe
from frappe import _
from frappe.model.document import Document


class StructureMounting(Document):
    def validate(self):
        """Light validation only. No workflow logic here."""
        self.validate_vendor_assignment()

    def on_update(self):
        """React to workflow transitions, not UI actions."""
        if self.workflow_state == "Approved":
            self.handle_approval()

    # ------------------------------------------------------------------
    # VALIDATIONS
    # ------------------------------------------------------------------
    def validate_vendor_assignment(self):
        if self.workflow_state != "Draft" and not self.assigned_vendor:
            frappe.throw(_("Assigned Vendor is mandatory before proceeding."))

    # ------------------------------------------------------------------
    # APPROVAL HANDLING
    # ------------------------------------------------------------------
    def handle_approval(self):
        """Executed once when Structure Mounting is Approved."""
        if self.structure_completion_status == "Done":
            return

        frappe.db.set_value(
            "Structure Mounting",
            self.name,
            "structure_completion_status",
            "Done",
            update_modified=False
        )

        panel_installation = self.create_panel_installation_if_missing()

        if panel_installation:
            frappe.db.set_value(
                "Structure Mounting",
                self.name,
                "linked_panel_installation",
                panel_installation.name,
                update_modified=False
            )

        frappe.db.commit()
        self.log_approval(panel_installation)

    def create_panel_installation_if_missing(self):
        existing = frappe.db.exists(
            "Panel Installation",
            {"job_file": self.job_file}
        )

        if existing:
            return frappe.get_doc("Panel Installation", existing)

        doc = frappe.get_doc({
            "doctype": "Panel Installation",
            "job_file": self.job_file,
            "lead": self.lead,
            "project": self.project,
            "assigned_vendor": self.assigned_vendor,
            "structure_mounting": self.name,
            "workflow_state": "Draft"
        })

        doc.flags.ignore_permissions = True
        doc.insert()

        frappe.msgprint(
            _(f"Panel Installation {doc.name} created"),
            indicator="green",
            alert=True
        )

        return doc

    def log_approval(self, panel_installation=None):
        message = "Structure Mounting approved."
        if panel_installation:
            message += f" Panel Installation {panel_installation.name} created."

        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Structure Mounting",
            "reference_name": self.name,
            "content": _(message)
        }).insert(ignore_permissions=True)
