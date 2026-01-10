# Copyright (c) 2025, KaitenSoftware
# Role-Based Access Control Setup
# Creates/verifies all required roles for Solar ERP

import frappe
from frappe import _


# Define all required roles for the RBAC system
REQUIRED_ROLES = [
    {
        "role_name": "Sales Executive",
        "desk_access": 1,
        "is_custom": 1,
        "description": "Can create/update Leads, initiate Job Case, view execution status (read-only)"
    },
    {
        "role_name": "Sales Manager",
        "desk_access": 1,
        "is_custom": 1,
        "description": "Can send/approve/revise Quotations, create Sales Order"
    },
    {
        "role_name": "Vendor Executive",
        "desk_access": 1,
        "is_custom": 1,
        "description": "Can Start, Update, Upload Photos, Submit, Hold execution stages"
    },
    {
        "role_name": "Project Manager",
        "desk_access": 1,
        "is_custom": 1,
        "description": "Can Approve, Rework, Close, Reopen execution stages"
    },
    {
        "role_name": "Inventory Manager",
        "desk_access": 1,
        "is_custom": 1,
        "description": "Can view Material Requests, Warehouse Stock, Sales Orders (read-only)"
    },
    {
        "role_name": "Purchase Manager",
        "desk_access": 1,
        "is_custom": 1,
        "description": "Can create Purchase Orders, select Vendors, approve POs, create Purchase Receipts"
    },
    {
        "role_name": "Accounts Manager",
        "desk_access": 1,
        "is_custom": 1,
        "description": "Can handle Advance Payment, Payment Entry, Purchase/Sales Invoice"
    }
]


def create_roles():
    """
    Create or verify all required roles for Solar ERP RBAC system
    """
    created = []
    existing = []
    
    for role_def in REQUIRED_ROLES:
        role_name = role_def["role_name"]
        
        if frappe.db.exists("Role", role_name):
            existing.append(role_name)
            # Update description if needed
            frappe.db.set_value("Role", role_name, "desk_access", role_def.get("desk_access", 1))
        else:
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": role_def.get("desk_access", 1),
                "is_custom": role_def.get("is_custom", 1),
                "disabled": 0
            })
            role.insert(ignore_permissions=True)
            created.append(role_name)
    
    frappe.db.commit()
    
    return {
        "created": created,
        "existing": existing,
        "message": _("Roles setup complete. Created: {0}, Already existing: {1}").format(
            len(created), len(existing)
        )
    }


@frappe.whitelist()
def setup_roles():
    """
    Whitelisted API to create roles
    """
    if not frappe.has_permission("Role", "create"):
        frappe.throw(_("Not permitted to create roles"))
    
    return create_roles()


def get_role_permissions_map():
    """
    Returns the permission mapping for each role across doctypes
    """
    return {
        "Vendor Executive": {
            # Execution DocTypes - can read/write, no create (auto-created)
            "Technical Survey": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Structure Mounting": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Panel Installation": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Meter Installation": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Meter Commissioning": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Verification Handover": {"read": 1, "write": 1, "create": 0, "delete": 0},
            # Job File - read only
            "Job File": {"read": 1, "write": 0, "create": 0, "delete": 0},
        },
        "Project Manager": {
            # Execution DocTypes - can read/write for approval
            "Technical Survey": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Structure Mounting": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Panel Installation": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Meter Installation": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Meter Commissioning": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Verification Handover": {"read": 1, "write": 1, "create": 0, "delete": 0},
            # Job File - read/write
            "Job File": {"read": 1, "write": 1, "create": 0, "delete": 0},
            # Sales - read only for tracking
            "Lead": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Quotation": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Sales Order": {"read": 1, "write": 0, "create": 0, "delete": 0},
        },
        "Sales Executive": {
            # CRM - can create/update Leads
            "Lead": {"read": 1, "write": 1, "create": 1, "delete": 0},
            # Execution - read only for status tracking
            "Technical Survey": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Structure Mounting": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Panel Installation": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Meter Installation": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Meter Commissioning": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Verification Handover": {"read": 1, "write": 0, "create": 0, "delete": 0},
            # Job File - read only
            "Job File": {"read": 1, "write": 0, "create": 0, "delete": 0},
            # Quotation - read only (cannot send)
            "Quotation": {"read": 1, "write": 0, "create": 0, "delete": 0},
        },
        "Sales Manager": {
            # CRM - full access
            "Lead": {"read": 1, "write": 1, "create": 1, "delete": 1},
            # Quotation - can create, send, approve
            "Quotation": {"read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1},
            # Sales Order - can create
            "Sales Order": {"read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1},
            # Execution - read only
            "Technical Survey": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Structure Mounting": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Panel Installation": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Meter Installation": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Meter Commissioning": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Verification Handover": {"read": 1, "write": 0, "create": 0, "delete": 0},
            # Job File - read only
            "Job File": {"read": 1, "write": 0, "create": 0, "delete": 0},
        },
        "Inventory Manager": {
            # Stock - read only
            "Material Request": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Stock Entry": {"read": 1, "write": 0, "create": 0, "delete": 0},
            "Sales Order": {"read": 1, "write": 0, "create": 0, "delete": 0},
            # Warehouse visibility handled separately
        },
        "Purchase Manager": {
            # Procurement - full access
            "Material Request": {"read": 1, "write": 1, "create": 0, "delete": 0},
            "Purchase Order": {"read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1},
            "Purchase Receipt": {"read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1},
            "Supplier": {"read": 1, "write": 1, "create": 1, "delete": 0},
        },
        "Accounts Manager": {
            # Accounts - full access
            "Payment Entry": {"read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1},
            "Sales Invoice": {"read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1},
            "Purchase Invoice": {"read": 1, "write": 1, "create": 1, "delete": 0, "submit": 1},
            # Quotation - read for payment tracking
            "Quotation": {"read": 1, "write": 0, "create": 0, "delete": 0},
            # Sales Order - read only (cannot create)
            "Sales Order": {"read": 1, "write": 0, "create": 0, "delete": 0},
        }
    }
