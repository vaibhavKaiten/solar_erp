import frappe

def execute():
    """Fix workflow allow_edit for In Progress state"""
    wf_name = "Structure Mounting Workflow"
    
    # Get the workflow document
    wf = frappe.get_doc("Workflow", wf_name)
    
    print(f"=== Current Workflow States ===")
    for state in wf.states:
        print(f"State: {state.state}, Allow Edit: {state.allow_edit}")
    
    # Update the "In Progress" state to allow Executive to edit
    for state in wf.states:
        if state.state == "In Progress":
            state.allow_edit = "Structure Mounting Executive"
            print(f"\n>>> Updated 'In Progress' state: allow_edit = 'Structure Mounting Executive'")
    
    wf.save()
    frappe.db.commit()
    
    print(f"\n=== Updated Workflow States ===")
    wf.reload()
    for state in wf.states:
        print(f"State: {state.state}, Allow Edit: {state.allow_edit}")
    
    print(f"\nWorkflow updated successfully!")
