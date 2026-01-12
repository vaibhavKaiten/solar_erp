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
        """Trigger auto-creation of Project Installation when approved"""
        previous_status = getattr(self, '_previous_status', None)
        
        # Check if status changed to Approved
        if self.status == "Approved" and previous_status != "Approved":
            self.handle_approval()
    
    def handle_approval(self):
        """Handle Structure Mounting approval - create Project Installation and update status"""
        # Set structure completion status to Done
        frappe.db.set_value("Structure Mounting", self.name, "structure_completion_status", "Done", update_modified=False)
        
        # Create Project Installation if it doesn't exist
        project_installation = self.create_project_installation_if_not_exists()
        
        # Link the Project Installation
        if project_installation:
            frappe.db.set_value("Structure Mounting", self.name, "linked_project_installation", project_installation.name, update_modified=False)
        
        # Commit the transaction
        frappe.db.commit()
        
        # Log audit entry
        self.log_approval_audit(project_installation)
    
    def create_project_installation_if_not_exists(self):
        """Create Project Installation record if it doesn't exist for this Job File"""
        # Check if Project Installation already exists for this Job File
        existing_pi = frappe.db.exists("Project Installation", {"job_file": self.job_file})
        
        if existing_pi:
            frappe.msgprint(
                _("Project Installation {0} already exists for Job File {1}").format(existing_pi, self.job_file),
                alert=True
            )
            return frappe.get_doc("Project Installation", existing_pi)
        
        # Create new Project Installation
        project_installation = frappe.get_doc({
            "doctype": "Project Installation",
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
        
        project_installation.flags.ignore_permissions = True
        project_installation.insert()
        
        frappe.msgprint(
            _("Project Installation {0} created successfully").format(project_installation.name),
            alert=True,
            indicator="green"
        )
        
        return project_installation
    
    def log_approval_audit(self, project_installation=None):
        """Log audit entry for Structure Mounting approval"""
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Structure Mounting",
            "reference_name": self.name,
            "content": _("Structure Mounting approved. Completion status set to Done.{0}").format(
                _(" Project Installation {0} created.").format(project_installation.name) if project_installation else ""
            )
        }).insert(ignore_permissions=True)

    @frappe.whitelist()
    def fix_project_installation_link(self):
        """Manually trigger linking of Project Installation"""
        if self.status != "Approved":
            frappe.throw(_("Can only fix link when status is Approved"))
        
        # This re-runs the linking logic
        self.handle_approval()
        return {"status": "success", "message": _("Link fixed successfully")}
