import frappe

# Create Execution Manager role
if not frappe.db.exists('Role', 'Execution Manager'):
    role = frappe.get_doc({'doctype': 'Role', 'role_name': 'Execution Manager', 'desk_access': 1, 'disabled': 0})
    role.insert(ignore_permissions=True)
    frappe.db.commit()
    print("✓ Created Execution Manager role")
else:
    print("✓ Execution Manager role already exists")
