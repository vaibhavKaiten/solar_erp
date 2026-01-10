"""
Utility to link Vendor Manager users to their Supplier companies
This should be run once to ensure all vendor managers are properly linked
"""

import frappe
from frappe import _


@frappe.whitelist()
def link_vendor_managers_to_suppliers():
    """
    Find all users with Vendor Manager role and ensure their Contact
    is linked to a Supplier via Dynamic Link
    
    This is a one-time setup utility
    """
    
    # Get all users with Vendor Manager role
    vendor_managers = frappe.db.sql("""
        SELECT DISTINCT u.name, u.full_name, u.email
        FROM `tabUser` u
        INNER JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE hr.role = 'Vendor Manager'
            AND u.enabled = 1
    """, as_dict=True)
    
    results = {
        "total": len(vendor_managers),
        "linked": 0,
        "already_linked": 0,
        "no_contact": 0,
        "errors": []
    }
    
    for user in vendor_managers:
        try:
            # Get contact for this user
            contact_name = frappe.db.get_value("Contact", {"user": user.name}, "name")
            
            if not contact_name:
                results["no_contact"] += 1
                results["errors"].append({
                    "user": user.name,
                    "error": "No Contact linked to user"
                })
                continue
            
            contact = frappe.get_doc("Contact", contact_name)
            
            # Check if already linked to a Supplier
            existing_link = None
            for link in contact.links:
                if link.link_doctype == "Supplier":
                    existing_link = link.link_name
                    break
            
            if existing_link:
                results["already_linked"] += 1
                frappe.logger().info(f"User {user.name} already linked to Supplier {existing_link}")
                continue
            
            # Need to link - but to which supplier?
            # This requires manual intervention or additional logic
            results["errors"].append({
                "user": user.name,
                "error": "Contact exists but not linked to any Supplier - manual linking required"
            })
            
        except Exception as e:
            results["errors"].append({
                "user": user.name,
                "error": str(e)
            })
    
    return results


@frappe.whitelist()
def link_contact_to_supplier(contact_name, supplier_name):
    """
    Link a specific Contact to a Supplier via Dynamic Link
    
    Args:
        contact_name: Name of the Contact document
        supplier_name: Name of the Supplier document
    
    Returns:
        dict: Success/error response
    """
    try:
        # Validate Contact exists
        if not frappe.db.exists("Contact", contact_name):
            return {
                "success": False,
                "error": _("Contact {0} does not exist").format(contact_name)
            }
        
        # Validate Supplier exists
        if not frappe.db.exists("Supplier", supplier_name):
            return {
                "success": False,
                "error": _("Supplier {0} does not exist").format(supplier_name)
            }
        
        contact = frappe.get_doc("Contact", contact_name)
        
        # Check if already linked
        for link in contact.links:
            if link.link_doctype == "Supplier" and link.link_name == supplier_name:
                return {
                    "success": True,
                    "message": _("Contact {0} is already linked to Supplier {1}").format(
                        contact_name, supplier_name
                    ),
                    "already_linked": True
                }
        
        # Add the link
        contact.append("links", {
            "link_doctype": "Supplier",
            "link_name": supplier_name
        })
        
        contact.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "message": _("Contact {0} successfully linked to Supplier {1}").format(
                contact_name, supplier_name
            ),
            "already_linked": False
        }
        
    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Error linking Contact {contact_name} to Supplier {supplier_name}"
        )
        return {
            "success": False,
            "error": _("Error linking contact: {0}").format(str(e))
        }


def get_vendor_managers_for_supplier(supplier_name):
    """
    Get all vendor manager users who should be linked to a specific supplier
    
    This checks User Permissions to find which vendor managers are assigned
    to territories where this supplier operates
    
    Args:
        supplier_name: Name of the Supplier
    
    Returns:
        list: List of user emails
    """
    
    # Get territories where this supplier is active
    territories = frappe.db.sql("""
        SELECT territory
        FROM `tabSupplier Territory Child Table`
        WHERE parent = %s AND status = 'Active'
    """, (supplier_name,), as_dict=True)
    
    if not territories:
        return []
    
    territory_list = [t.territory for t in territories]
    
    # Get vendor managers who have permissions for these territories
    vendor_managers = frappe.db.sql("""
        SELECT DISTINCT u.name, u.email
        FROM `tabUser` u
        INNER JOIN `tabHas Role` hr ON hr.parent = u.name
        INNER JOIN `tabUser Permission` up ON up.user = u.name
        WHERE hr.role = 'Vendor Manager'
            AND up.allow = 'Territory'
            AND up.for_value IN %(territories)s
            AND u.enabled = 1
    """, {"territories": territory_list}, as_dict=True)
    
    return [vm.email for vm in vendor_managers]
