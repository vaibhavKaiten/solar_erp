import frappe

def create_roles_and_check_docs():
    """Create roles and check Meter Commissioning documents"""
    frappe.init(site='rgespdev.koristu.app')
    frappe.connect()
    
    # Define roles to create
    roles_to_create = [
        "Meter Commissioning Executive",
        "Meter Commissioning Manager",
        "Verification Handover Executive",
        "Verification Handover Manager"
    ]
    
    print("\n=== CREATING ROLES ===")
    for role_name in roles_to_create:
        if not frappe.db.exists("Role", role_name):
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1
            })
            role.insert(ignore_permissions=True)
            print(f"✅ Created role: {role_name}")
        else:
            print(f"✓ Role already exists: {role_name}")
    
    frappe.db.commit()
    
    print("\n=== METER COMMISSIONING DOCUMENTS ===")
    mc_docs = frappe.db.get_all("Meter Commissioning", 
                                 fields=["name", "status", "job_file", "meter_installation"],
                                 limit=5)
    print(f"Total Meter Commissioning documents: {len(mc_docs)}")
    for doc in mc_docs:
        print(f"  - {doc.name}: Status={doc.status}, MI={doc.meter_installation}")
    
    print("\n=== RECENT METER INSTALLATIONS ===")
    mi_docs = frappe.db.get_all("Meter Installation",
                                fields=["name", "status", "job_file", "linked_meter_commissioning"],
                                order_by="modified desc",
                                limit=5)
    for doc in mi_docs:
        print(f"  - {doc.name}: Status={doc.status}, Linked MC={doc.linked_meter_commissioning or 'None'}")
    
    frappe.destroy()

if __name__ == "__main__":
    create_roles_and_check_docs()
