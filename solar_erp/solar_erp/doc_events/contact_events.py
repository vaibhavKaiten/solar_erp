"""
Contact event handlers for automatic Supplier linking
Automatically links Contacts to Suppliers when portal users are created
"""

import frappe
from frappe import _


def auto_link_contact_to_supplier(doc, method=None):
    """
    Automatically link Contact to Supplier when:
    1. Contact is created from Supplier form
    2. Contact has a user with Vendor Manager or Vendor Executive role
    
    This hook is called on Contact after_insert and on_update
    
    NOTE: This is currently disabled to prevent "document modified" errors.
    Contact linking is now handled in the create_vendor_portal_user API method.
    
    Args:
        doc: Contact document
        method: Event method (after_insert, on_update, etc.)
    """
    
    # Disabled - linking is handled in API method
    pass


def link_contact_on_user_role_change(doc, method=None):
    """
    Link Contact to Supplier when a user is assigned Vendor Manager or Vendor Executive role
    
    This hook is called on User after roles are updated
    
    Args:
        doc: User document
        method: Event method
    """
    
    # Get user roles
    user_roles = [role.role for role in doc.roles]
    vendor_roles = ["Vendor Manager", "Vendor Executive"]
    
    has_vendor_role = any(role in user_roles for role in vendor_roles)
    
    if not has_vendor_role:
        return
    
    # Find contact for this user
    contact_name = frappe.db.get_value("Contact", {"user": doc.name}, "name")
    
    if not contact_name:
        frappe.logger().info(f"No Contact found for user {doc.name}")
        return
    
    contact = frappe.get_doc("Contact", contact_name)
    
    # Check if already linked to a Supplier
    for link in contact.links:
        if link.link_doctype == "Supplier":
            frappe.logger().info(f"Contact {contact_name} already linked to Supplier {link.link_name}")
            return
    
    # If not linked, show a message to admin
    frappe.msgprint(
        _("User {0} has been assigned a Vendor role but their Contact is not linked to any Supplier. "
          "Please link Contact {1} to a Supplier in the Contact form.").format(
            doc.name, contact_name
        ),
        indicator="orange",
        alert=True
    )
