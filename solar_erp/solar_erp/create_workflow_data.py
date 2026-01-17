import frappe
from frappe.model.naming import make_autoname

def execute():
    # 1. Create Role: Installation Vendor and Common Team Role
    roles = ["Installation Vendor", "Structure Mounting Team"]
    for r in roles:
        if not frappe.db.exists("Role", r):
            role = frappe.new_doc("Role")
            role.role_name = r
            role.desk_access = 1
            role.save()
            frappe.db.commit()

    # 2. Ensure Workflow States exist
    states = ["Draft", "In Progress", "On Hold", "Submitted", "Approved", "Rejected"]
    for s in states:
        if not frappe.db.exists("Workflow State", s):
            doc = frappe.new_doc("Workflow State")
            doc.workflow_state_name = s
            # Optional styles
            if s == "Approved": doc.style = "Success"
            elif s == "Rejected": doc.style = "Danger"
            elif s == "On Hold": doc.style = "Warning"
            elif s == "Submitted": doc.style = "Primary"
            elif s == "In Progress": doc.style = "Info"
            doc.save()
            
    # 2b. Ensure Workflow Actions exist (Link field requirement)
    actions = ["Start Mounting", "Put On Hold", "Resume", "Submit Mounting", "Approve", "Reject", "Restart"]
    for a in actions:
        if not frappe.db.exists("Workflow Action Master", a):
             try:
                 doc = frappe.new_doc("Workflow Action Master")
                 doc.workflow_action_name = a
                 doc.save()
             except Exception:
                 pass
                 
    frappe.db.commit()

    # 3. Create/Update Workflow
    wf_name = "Structure Mounting Workflow"
    if frappe.db.exists("Workflow", wf_name):
        frappe.delete_doc("Workflow", wf_name)

    wf = frappe.new_doc("Workflow")
    wf.workflow_name = wf_name
    wf.document_type = "Structure Mounting"
    wf.is_active = 1
    wf.workflow_state_field = "status"
    
    # States
    # Draft: Executive
    wf.append("states", {"state": "Draft", "doc_status": 0, "allow_edit": "Structure Mounting Executive"})
    
    # In Progress: Structure Mounting Team (Common Role for Exec + Vendor)
    wf.append("states", {"state": "In Progress", "doc_status": 0, "allow_edit": "Structure Mounting Team"})
    
    # On Hold: Executive
    wf.append("states", {"state": "On Hold", "doc_status": 0, "allow_edit": "Structure Mounting Executive"})
    
    # Submitted: Manager
    wf.append("states", {"state": "Submitted", "doc_status": 0, "allow_edit": "Structure Mounting Manager"})
    
    # Approved: Final. System Manager.
    wf.append("states", {"state": "Approved", "doc_status": 1, "update_field": "status", "update_value": "Approved", "allow_edit": "System Manager"})
    
    # Rejected: Executive
    wf.append("states", {"state": "Rejected", "doc_status": 0, "allow_edit": "Structure Mounting Executive"})
    
    # Transitions
    transitions = []

    # 1. Start Mounting: Draft -> In Progress (Executive)
    wf.append("transitions", {
        "state": "Draft",
        "action": "Start Mounting",
        "next_state": "In Progress",
        "allowed": "Structure Mounting Executive",
        "allow_self_approval": 1
    })
    
    # 2. Put On Hold: In Progress -> On Hold (Executive)
    wf.append("transitions", {
        "state": "In Progress",
        "action": "Put On Hold",
        "next_state": "On Hold",
        "allowed": "Structure Mounting Executive",
        "allow_self_approval": 1
    })

    # 3. Resume: On Hold -> In Progress (Executive)
    wf.append("transitions", {
        "state": "On Hold",
        "action": "Resume",
        "next_state": "In Progress",
        "allowed": "Structure Mounting Executive",
        "allow_self_approval": 1
    })

    # 4. Submit Mounting: In Progress -> Submitted (Executive)
    wf.append("transitions", {
        "state": "In Progress",
        "action": "Submit Mounting",
        "next_state": "Submitted",
        "allowed": "Structure Mounting Executive",
        "allow_self_approval": 1
    })

    # 5. Approve: Submitted -> Approved (Manager)
    wf.append("transitions", {
        "state": "Submitted",
        "action": "Approve",
        "next_state": "Approved",
        "allowed": "Structure Mounting Manager",
        "allow_self_approval": 1
    })

    # 6. Reject: Submitted -> Rejected (Manager)
    wf.append("transitions", {
        "state": "Submitted",
        "action": "Reject",
        "next_state": "Rejected",
        "allowed": "Structure Mounting Manager",
        "allow_self_approval": 1
    })

    # 7. Restart: Rejected -> In Progress (Executive)
    wf.append("transitions", {
        "state": "Rejected",
        "action": "Restart",
        "next_state": "In Progress",
        "allowed": "Structure Mounting Executive",
        "allow_self_approval": 1
    })

    wf.save()
    frappe.db.commit()
    print("Workflow 'Structure Mounting Workflow' created successfully.")
