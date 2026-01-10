"""
Technical Survey Permission Control
Restricts visibility so vendors can only see surveys assigned to their company
"""

import frappe
from frappe import _
from solar_erp.solar_erp.utils.vendor_permissions import get_user_supplier


def get_permission_query_conditions(user):
    """
    Apply record-level filtering for Technical Survey list view
    
    This function is called when fetching lists of Technical Survey documents.
    It returns a SQL WHERE clause that filters the results based on user role.
    
    Vendor permissions are now company-based:
    - Vendor Manager: Can see ALL surveys assigned to their supplier company
    - Vendor Executive: Can only see surveys explicitly assigned to them
    
    Args:
        user: User email (frappe.session.user)
    
    Returns:
        SQL WHERE clause or None (None = no restriction)
    """
    
    if not user:
        user = frappe.session.user
    
    # Skip restriction for Administrator
    if user == "Administrator":
        return None
    
    # Get user roles (convert to lowercase for comparison)
    user_roles = [role.lower() for role in frappe.get_roles(user)]
    
    # Internal roles that can see all Technical Surveys (lowercase)
    internal_roles = [
        "system manager",
        "project manager", 
        "technical survey manager",
        "installation manager",
        "service head"
    ]
    
    # If user has any internal role, no restriction
    if any(role in user_roles for role in internal_roles):
        return None
    
    # Vendor roles - use company-based filtering
    vendor_manager_roles = ["vendor manager", "site visit vendor manager"]
    vendor_exec_roles = ["vendor executive", "site visit vendor executive"]
    
    # Get supplier company linked to this user via Contact
    vendor_company = get_user_supplier(user)
    
    frappe.logger().info(f"Permission check for user {user}: vendor_company = {vendor_company}")
    
    if not vendor_company:
        # User not linked to any supplier company - no access
        frappe.logger().info(f"User {user} has no vendor company linked")
        return "`tabTechnical Survey`.name = ''"
    
    # Vendor Manager → all surveys assigned to their company (excluding Draft)
    if any(r in user_roles for r in vendor_manager_roles):
        query = (
            f"`tabTechnical Survey`.assigned_vendor = "
            f"{frappe.db.escape(vendor_company)} AND "
            f"`tabTechnical Survey`.status != 'Draft'"
        )
        frappe.logger().info(f"Vendor Manager {user} query: {query}")
        return query
    
    # Vendor Executive → only surveys explicitly assigned to them (excluding Draft)
    if any(r in user_roles for r in vendor_exec_roles):
        query = (
            f"`tabTechnical Survey`.custom_technical_executive = "
            f"{frappe.db.escape(user)} AND "
            f"`tabTechnical Survey`.assigned_vendor = "
            f"{frappe.db.escape(vendor_company)} AND "
            f"`tabTechnical Survey`.status != 'Draft'"
        )
        frappe.logger().info(f"Vendor Executive {user} query: {query}")
        return query
    
    # No matching vendor role - no access
    frappe.logger().info(f"User {user} has no vendor role")
    return "`tabTechnical Survey`.name = ''"



def has_permission(doc, ptype, user):
    """
    Check if user has permission to access a specific Technical Survey document
    
    This function is called when:
    - Opening a document directly via URL
    - Checking read/write/delete permissions
    
    Company-based permissions:
    - Vendor Manager: Can access all surveys for their supplier company
    - Vendor Executive: Can only access surveys explicitly assigned to them
    
    Args:
        doc: Technical Survey document or doctype string
        ptype: Permission type ('read', 'write', 'submit', etc.)
        user: User email (frappe.session.user)
    
    Returns:
        True if allowed, False if denied
    """
    
    if not user:
        user = frappe.session.user
    
    # Administrator always has access
    if user == "Administrator":
        return True
    
    # Get user roles (lowercase for comparison)
    user_roles = [role.lower() for role in frappe.get_roles(user)]
    
    # Internal roles have full access (lowercase)
    internal_roles = [
        "system manager",
        "project manager",
        "technical survey manager",
        "installation manager",
        "service head"
    ]
    
    if any(role in user_roles for role in internal_roles):
        return True
    
    # Vendor roles - check company-based access
    vendor_manager_roles = ["vendor manager", "site visit vendor manager"]
    vendor_exec_roles = ["vendor executive", "site visit vendor executive"]
    
    if any(role in user_roles for role in vendor_manager_roles + vendor_exec_roles):
        # If doc is a string (doctype name), we can't check assignment
        # Allow at doctype level, individual docs will be filtered by query conditions
        if isinstance(doc, str):
            return True
        
        # Get user's supplier company
        vendor_company = get_user_supplier(user)
        
        if not vendor_company:
            frappe.msgprint(
                _("You do not have permission to access Technical Surveys. "
                  "Your user account is not linked to any vendor company."),
                indicator="red",
                raise_exception=True
            )
            return False
        
        # Check if document is assigned to user's company
        doc_vendor_company = doc.get("assigned_vendor") if hasattr(doc, 'get') else getattr(doc, 'assigned_vendor', None)
        
        if doc_vendor_company != vendor_company:
            frappe.msgprint(
                _("You do not have permission to access this Technical Survey. "
                  "It is assigned to {0}, but you belong to {1}.").format(
                    doc_vendor_company or "another vendor", vendor_company
                ),
                indicator="red",
                raise_exception=True
            )
            return False
        
        # Vendor Manager → can access all company surveys
        if any(r in user_roles for r in vendor_manager_roles):
            return True
        
        # Vendor Executive → only if explicitly assigned
        if any(r in user_roles for r in vendor_exec_roles):
            assigned_executive = doc.get("custom_technical_executive") if hasattr(doc, 'get') else getattr(doc, 'custom_technical_executive', None)
            
            if assigned_executive == user:
                return True
            else:
                frappe.msgprint(
                    _("This Technical Survey has not been assigned to you yet. "
                      "Please contact your Vendor Manager to get this survey assigned."),
                    indicator="orange",
                    raise_exception=True
                )
                return False
    
    # No matching role - deny access
    return False



def on_trash(doc, method=None):
    """
    Prevent vendors from deleting Technical Survey documents
    Only allow internal roles to delete
    """
    user = frappe.session.user
    
    if user == "Administrator":
        return
    
    user_roles = [role.lower() for role in frappe.get_roles(user)]
    
    # Only these roles can delete (lowercase)
    can_delete_roles = [
        "system manager",
        "project manager",
        "technical survey manager"
    ]
    
    if not any(role in user_roles for role in can_delete_roles):
        frappe.throw(
            _("You do not have permission to delete Technical Survey documents."),
            frappe.PermissionError
        )
