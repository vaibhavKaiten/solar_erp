# Copyright (c) 2025, KaitenSoftware
# User Setup Script
# Creates/verifies users and assigns roles for Solar ERP

import frappe
from frappe import _
from frappe.utils import random_string


# Define user-role mappings
USER_ROLE_MAPPINGS = [
    {
        "email": "sales@koristu.app",
        "first_name": "Sales",
        "last_name": "Executive",
        "roles": ["Sales Executive"],
        "description": "Sales team member"
    },
    {
        "email": "salesmanager@koristu.app",
        "first_name": "Sales",
        "last_name": "Manager",
        "roles": ["Sales Manager"],
        "description": "Sales department manager"
    },
    {
        "email": "shreeji@koristu.app",
        "first_name": "Shreeji",
        "last_name": "Vendor Executive",
        "roles": ["Vendor Executive"],
        "description": "Vendor execution team - handles all execution stages"
    },
    {
        "email": "projectmanager@koristu.app",
        "first_name": "Project",
        "last_name": "Manager",
        "roles": ["Project Manager"],
        "description": "Approves/manages execution stages"
    },
    {
        "email": "inventory@koristu.app",
        "first_name": "Inventory",
        "last_name": "Manager",
        "roles": ["Inventory Manager"],
        "description": "Manages warehouse and stock"
    },
    {
        "email": "purchase@koristu.app",
        "first_name": "Purchase",
        "last_name": "Manager",
        "roles": ["Purchase Manager"],
        "description": "Handles procurement and vendor selection"
    },
    {
        "email": "accounts@koristu.app",
        "first_name": "Accounts",
        "last_name": "Manager",
        "roles": ["Accounts Manager"],
        "description": "Handles payments and invoicing"
    }
]


def create_users():
    """
    Create or verify users and assign roles
    Returns summary of created/updated users
    """
    created = []
    updated = []
    errors = []
    
    for user_def in USER_ROLE_MAPPINGS:
        try:
            email = user_def["email"]
            
            if frappe.db.exists("User", email):
                # User exists - update roles
                user = frappe.get_doc("User", email)
                
                # Add missing roles
                existing_roles = [r.role for r in user.roles]
                roles_added = []
                
                for role_name in user_def["roles"]:
                    if role_name not in existing_roles:
                        user.append("roles", {"role": role_name})
                        roles_added.append(role_name)
                
                if roles_added:
                    user.save(ignore_permissions=True)
                    updated.append({
                        "user": email,
                        "roles_added": roles_added
                    })
                else:
                    updated.append({
                        "user": email,
                        "roles_added": [],
                        "note": "All roles already assigned"
                    })
            else:
                # Create new user
                user = frappe.get_doc({
                    "doctype": "User",
                    "email": email,
                    "first_name": user_def["first_name"],
                    "last_name": user_def.get("last_name", ""),
                    "enabled": 1,
                    "user_type": "System User",
                    "send_welcome_email": 0,  # Don't send email during setup
                    "new_password": random_string(10)  # Temporary password
                })
                
                # Add roles
                for role_name in user_def["roles"]:
                    user.append("roles", {"role": role_name})
                
                user.insert(ignore_permissions=True)
                created.append({
                    "user": email,
                    "roles": user_def["roles"]
                })
                
        except Exception as e:
            errors.append({
                "user": user_def["email"],
                "error": str(e)
            })
    
    frappe.db.commit()
    
    return {
        "created": created,
        "updated": updated,
        "errors": errors,
        "message": _("User setup complete. Created: {0}, Updated: {1}, Errors: {2}").format(
            len(created), len(updated), len(errors)
        )
    }


@frappe.whitelist()
def setup_users():
    """
    Whitelisted API to create/update users
    """
    if not frappe.has_permission("User", "create"):
        frappe.throw(_("Not permitted to create users"))
    
    return create_users()


def get_user_for_role(role_name):
    """
    Get users with a specific role
    """
    return frappe.get_all(
        "Has Role",
        filters={"role": role_name, "parenttype": "User"},
        fields=["parent as user"]
    )


def assign_role_to_user(email, role_name):
    """
    Assign a single role to a user
    """
    if not frappe.db.exists("User", email):
        frappe.throw(_("User {0} does not exist").format(email))
    
    if not frappe.db.exists("Role", role_name):
        frappe.throw(_("Role {0} does not exist").format(role_name))
    
    user = frappe.get_doc("User", email)
    existing_roles = [r.role for r in user.roles]
    
    if role_name not in existing_roles:
        user.append("roles", {"role": role_name})
        user.save(ignore_permissions=True)
        frappe.db.commit()
        return True
    
    return False  # Already has role


def remove_role_from_user(email, role_name):
    """
    Remove a role from a user
    """
    if not frappe.db.exists("User", email):
        frappe.throw(_("User {0} does not exist").format(email))
    
    user = frappe.get_doc("User", email)
    user.roles = [r for r in user.roles if r.role != role_name]
    user.save(ignore_permissions=True)
    frappe.db.commit()
    return True
