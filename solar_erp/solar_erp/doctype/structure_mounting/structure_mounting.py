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
            frappe.db.set_value("Structure Mounting", self.name, "linked_panel_installation", project_installation.name, update_modified=False)
        
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

    @frappe.whitelist()
    def initiate_structure_mounting(self):
        """
        Initiate Structure Mounting for Vendor
        - Changes status to 'Assigned to Vendor'
        - Assigns document to the Vendor Manager of the assigned vendor
        """
        
        # 1. Validation
        if not (self.assigned_vendor):
             frappe.throw(_("Please assign a Vendor before initiating."))

        if self.status != "Draft":
             frappe.throw(_("Can only initiate when status is 'Draft'. Current status: {0}").format(self.status))
             
        # Check permissions (System Manager, Administrator, Structure Mounting Manager, Project Manager)
        roles = frappe.get_roles()
        allowed_roles = ["System Manager", "Administrator", "Structure Mounting Manager", "Project Manager"]
        
        has_permission = any(role in roles for role in allowed_roles)
        
        if not has_permission:
            frappe.throw(_("You do not have permission to initiate Structure Mounting."))

        # 2. Find Vendor Manager
        # Logic: Supplier -> Dynamic Link (Contact) -> Contact -> User -> Role 'Vendor Manager'
        
        contacts = frappe.db.sql("""
            SELECT dl.parent
            FROM `tabDynamic Link` dl
            WHERE dl.link_doctype = 'Supplier'
                AND dl.link_name = %s
                AND dl.parenttype = 'Contact'
        """, (self.assigned_vendor,), as_dict=True)
        
        contact_names = [c.parent for c in contacts]
        
        if not contact_names:
            frappe.throw(_("No contacts linked to Vendor {0}. Cannot identify Vendor Manager.").format(self.assigned_vendor))
            
        managers = frappe.db.sql("""
            SELECT DISTINCT u.name
            FROM `tabUser` u
            INNER JOIN `tabContact` c ON c.user = u.name
            INNER JOIN `tabHas Role` hr ON hr.parent = u.name
            WHERE hr.role = 'Vendor Manager'
                AND c.name IN %s
                AND u.enabled = 1
        """, (contact_names,), as_dict=True)
        
        if not managers:
             frappe.throw(_("No valid 'Vendor Manager' found for Vendor {0}. Please ensure a Contact is linked to a User with 'Vendor Manager' role.").format(self.assigned_vendor))

        # 3. Update Status
        self.status = "Assigned to Vendor"
        self.save(ignore_permissions=True)
        
        # 4. Assign ToDo to Vendor Manager(s)
        from frappe.desk.form.assign_to import add as add_assignment
        
        assigned_users = []
        for manager in managers:
            add_assignment({
                "assign_to": [manager.name],
                "doctype": "Structure Mounting",
                "name": self.name,
                "description": _("Structure Mounting {0} has been assigned to you.").format(self.name),
            })
            assigned_users.append(manager.name)
            
        frappe.msgprint(
            _("Structure Mounting Initiated. Assigned to: {0}").format(", ".join(assigned_users)),
            indicator='green',
            alert=True
        )
