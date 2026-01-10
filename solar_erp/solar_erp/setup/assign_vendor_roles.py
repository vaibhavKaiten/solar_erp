# Script to assign all execution roles to Shreeji vendor user
import frappe

def setup_shreeji_vendor():
    """Add all required roles to Shreeji Vendor Executive user"""
    
    user_email = "shreeji.vendor.executive@example.com"
    
    if not frappe.db.exists("User", user_email):
        print(f"User {user_email} not found!")
        return
    
    user = frappe.get_doc("User", user_email)
    
    # Roles to add
    roles_to_add = [
        # Main unified execution role
        "Vendor Executive",
        
        # Stage-specific roles (for backward compatibility)
        "Technical Survey Executive",
        "Structure Mounting Executive",
        "Panel Installation Executive",
        "Meter Installation Executive",
        "Meter Commissioning Executive",
        "Verification Handover Executive",
    ]
    
    # Get existing roles
    existing_roles = [r.role for r in user.roles]
    
    roles_added = []
    for role_name in roles_to_add:
        # First ensure the role exists
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
                "is_custom": 1
            }).insert(ignore_permissions=True)
            print(f"Created role: {role_name}")
        
        # Add role to user if not already assigned
        if role_name not in existing_roles:
            user.append("roles", {"role": role_name})
            roles_added.append(role_name)
    
    if roles_added:
        user.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"Added roles to {user_email}: {', '.join(roles_added)}")
    else:
        print(f"All roles already assigned to {user_email}")
    
    # Also set custom_territory to Jaipur for territory-based assignment
    frappe.db.set_value("User", user_email, "custom_territory", "Jaipur", update_modified=False)
    frappe.db.commit()
    print(f"Set territory to Jaipur for {user_email}")

if __name__ == "__main__":
    setup_shreeji_vendor()
