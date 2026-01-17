"""
Technical Survey Module Setup Script
Run with: bench --site rgespdev.koristu.app execute solar_erp.solar_erp.setup_technical_survey.setup_all
"""

import frappe
from frappe import _


def setup_all():
    """Run all setup functions"""
    print("Starting Technical Survey Module Setup...")
    
    # 1. Create custom territory field on User
    create_custom_territory_field()
    
    # 2. Create roles
    create_roles()
    
    # 3. Create test users
    create_test_users()
    
    # 4. Create Jaipur territory if not exists
    create_jaipur_territory()
    
    frappe.db.commit()
    print("Technical Survey Module Setup Complete!")


def create_custom_territory_field():
    """Add custom_territory field to User DocType"""
    print("Creating custom_territory field on User...")
    
    if not frappe.db.exists("Custom Field", {"dt": "User", "fieldname": "custom_territory"}):
        custom_field = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": "User",
            "fieldname": "custom_territory",
            "fieldtype": "Link",
            "label": "Territory",
            "options": "Territory",
            "insert_after": "location",
            "module": "Solar Project"
        })
        custom_field.insert(ignore_permissions=True)
        print("  Created custom_territory field on User")
    else:
        print("  custom_territory field already exists")


def create_roles():
    """Create Technical Survey roles"""
    print("Creating roles...")
    
    roles = [
        "Technical Survey Executive",
        "Technical Survey Manager"
    ]
    
    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
                "is_custom": 1
            })
            role.insert(ignore_permissions=True)
            print(f"  Created role: {role_name}")
        else:
            print(f"  Role already exists: {role_name}")


def create_jaipur_territory():
    """Create Jaipur territory if not exists"""
    print("Creating Jaipur territory...")
    
    if not frappe.db.exists("Territory", "Jaipur"):
        # Get parent territory
        parent = frappe.db.get_value("Territory", {"is_group": 1}, "name") or "All Territories"
        
        territory = frappe.get_doc({
            "doctype": "Territory",
            "territory_name": "Jaipur",
            "parent_territory": parent
        })
        territory.insert(ignore_permissions=True)
        print("  Created Jaipur territory")
    else:
        print("  Jaipur territory already exists")


def create_test_users():
    """Create test users for Technical Survey"""
    print("Creating test users...")
    
    # Shreeji Vendor Executive
    if not frappe.db.exists("User", "shreeji.vendor.executive@example.com"):
        user = frappe.get_doc({
            "doctype": "User",
            "email": "shreeji.vendor.executive@example.com",
            "first_name": "Shreeji Vendor",
            "last_name": "Executive",
            "enabled": 1,
            "new_password": "Test@1234",
            "send_welcome_email": 0,
            "roles": [
                {"role": "Technical Survey Executive"}
            ]
        })
        user.insert(ignore_permissions=True)
        
        # Set territory after insert
        frappe.db.set_value("User", user.name, "custom_territory", "Jaipur", update_modified=False)
        print("  Created user: shreeji.vendor.executive@example.com (Jaipur)")
    else:
        # Ensure role and territory are set
        frappe.db.set_value("User", "shreeji.vendor.executive@example.com", "custom_territory", "Jaipur", update_modified=False)
        print("  User already exists: shreeji.vendor.executive@example.com")
    
    # Project Manager
    if not frappe.db.exists("User", "project.manager@example.com"):
        user = frappe.get_doc({
            "doctype": "User",
            "email": "project.manager@example.com",
            "first_name": "Project",
            "last_name": "Manager",
            "enabled": 1,
            "new_password": "Test@1234",
            "send_welcome_email": 0,
            "roles": [
                {"role": "Technical Survey Manager"}
            ]
        })
        user.insert(ignore_permissions=True)
        print("  Created user: project.manager@example.com")
    else:
        print("  User already exists: project.manager@example.com")


if __name__ == "__main__":
    setup_all()
