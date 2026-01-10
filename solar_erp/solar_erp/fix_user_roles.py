import frappe

def execute():
    """Fix user roles using direct database operations"""
    
    print("=== Current User Roles ===")
    
    users = ["sme@sm.com", "smm@sm.com"]
    for user_email in users:
        roles = frappe.db.get_all("Has Role", filters={"parent": user_email}, fields=["role"])
        role_names = [r.role for r in roles]
        print(f"{user_email}: {role_names}")
    
    # Remove Manager role from Executive user (sme@sm.com)
    frappe.db.delete("Has Role", {
        "parent": "sme@sm.com",
        "role": "Structure Mounting Manager"
    })
    print(f"\n>>> Removed 'Structure Mounting Manager' role from sme@sm.com")
    
    # Remove Executive role from Manager user (smm@sm.com)
    frappe.db.delete("Has Role", {
        "parent": "smm@sm.com",
        "role": "Structure Mounting Executive"
    })
    print(f">>> Removed 'Structure Mounting Executive' role from smm@sm.com")
    
    frappe.db.commit()
    
    # Clear user cache
    frappe.clear_cache(user="sme@sm.com")
    frappe.clear_cache(user="smm@sm.com")
    
    print("\n=== Updated User Roles ===")
    for user_email in users:
        roles = frappe.db.get_all("Has Role", filters={"parent": user_email}, fields=["role"])
        role_names = [r.role for r in roles]
        print(f"{user_email}: {role_names}")
    
    print("\nUser roles fixed successfully!")
