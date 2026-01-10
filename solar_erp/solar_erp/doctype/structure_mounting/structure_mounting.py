# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StructureMounting(Document):
#     def validate(self):
#         """Validation before save"""
#         # Prevent manual creation - must be auto-created from Delivery Note
#         # Exception: System Manager can create manually for emergency/data migration scenarios
#         if self.is_new() and not frappe.flags.in_import:
#             # Check if this is being created via the auto-creation flow
#             if not getattr(frappe.local, 'auto_creating_structure_mounting', False):
#                 # Allow System Manager to create manually (emergency override)
#                 if not ("System Manager" in frappe.get_roles(frappe.session.user)):
#                     frappe.throw(
#                         _("""Structure Mounting cannot be created manually.
                        
# It will be automatically created when a Delivery Note is submitted for a Sales Order.

# If you need to create this manually, please contact your System Administrator."""),
#                         title=_("Manual Creation Not Allowed")
#                     )
#                 else:
#                     # System Manager is creating manually - log it
#                     frappe.msgprint(
#                         _("⚠️ You are creating Structure Mounting manually as System Manager. Ensure all required fields are filled correctly."),
#                         alert=True,
#                         indicator="orange"
#                     )
        
#         # Store previous status for change tracking
#         if not self.is_new():
#             self._previous_status = frappe.db.get_value("Structure Mounting", self.name, "status")
#         else:
#             self._previous_status = None
    
    def on_update(self):
        """Trigger auto-creation of Panel Installation when approved"""
        previous_status = getattr(self, '_previous_status', None)
        
        # Check if status changed to Approved
        if self.status == "Approved" and previous_status != "Approved":
            self.handle_approval()
    
    def handle_approval(self):
        """Handle Structure Mounting approval - create Panel Installation and update status"""
        # Set structure completion status to Done
        frappe.db.set_value("Structure Mounting", self.name, "structure_completion_status", "Done", update_modified=False)
        
        # Create Panel Installation if it doesn't exist
        panel_installation = self.create_panel_installation_if_not_exists()
        
        # Link the Panel Installation
        if panel_installation:
            frappe.db.set_value("Structure Mounting", self.name, "linked_panel_installation", panel_installation.name, update_modified=False)
        
        # Commit the transaction
        frappe.db.commit()
        
        # Log audit entry
        self.log_approval_audit(panel_installation)
    
    def create_panel_installation_if_not_exists(self):
        """Create Panel Installation record if it doesn't exist for this Job File"""
        # Check if Panel Installation already exists for this Job File
        existing_pi = frappe.db.exists("Panel Installation", {"job_file": self.job_file})
        
        if existing_pi:
            frappe.msgprint(
                _("Panel Installation {0} already exists for Job File {1}").format(existing_pi, self.job_file),
                alert=True
            )
            return frappe.get_doc("Panel Installation", existing_pi)
        
        # Create new Panel Installation
        panel_installation = frappe.get_doc({
            "doctype": "Panel Installation",
            "job_file": self.job_file,
            "lead": self.lead,
            "project": self.project,
            "assigned_vendor": self.assigned_vendor,
            "structure_mounting": self.name,
            "structure_type": self.structure_type,
            "anchoring_type": self.anchoring_type,
            "structure_height": self.structure_height_m,
            "status": "Draft"
        })
        
        panel_installation.flags.ignore_permissions = True
        panel_installation.insert()
        
        frappe.msgprint(
            _("Panel Installation {0} created successfully").format(panel_installation.name),
            alert=True,
            indicator="green"
        )
        
        return panel_installation
    
    def log_approval_audit(self, panel_installation=None):
        """Log audit entry for Structure Mounting approval"""
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Structure Mounting",
            "reference_name": self.name,
            "content": _("Structure Mounting approved. Completion status set to Done.{0}").format(
                _(" Panel Installation {0} created.").format(panel_installation.name) if panel_installation else ""
            )
        }).insert(ignore_permissions=True)

    @frappe.whitelist()
    def fix_panel_installation_link(self):
        """Manually trigger linking of Panel Installation"""
        if self.status != "Approved":
            frappe.throw(_("Can only fix link when status is Approved"))
        
        # This re-runs the linking logic
        self.handle_approval()
        return {"status": "success", "message": _("Link fixed successfully")}
