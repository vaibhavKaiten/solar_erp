#!/usr/bin/env python3
"""
Rename Technical Survey Workflow State "Assigned" to "Assigned to Vendor"
"""
import frappe

def rename_workflow_state():
    """Rename the Technical Survey workflow state 'Assigned' to 'Assigned to Vendor' and update transitions"""
    
    print("Starting Workflow State rename...")
    
    # 1. Get the Workflow document
    try:
        workflow = frappe.get_doc('Workflow', 'Technical Survey')
    except frappe.DoesNotExistError:
        print("Error: Workflow 'Technical Survey' not found!")
        return

    print("Current workflow states:")
    found_assigned = False
    for state in workflow.states:
        print(f"  State: '{state.state}' -> Update Value: '{state.update_value}'")
        if state.state == 'Assigned' or state.state == 'Assigned ': # Check for both
           found_assigned = True
    
    # Check/Create 'Assigned to Vendor' Workflow State
    if not frappe.db.exists("Workflow State", "Assigned to Vendor"):
        print("Creating new Workflow State 'Assigned to Vendor'...")
        new_state = frappe.new_doc("Workflow State")
        new_state.workflow_state_name = "Assigned to Vendor"
        new_state.insert()
        frappe.db.commit()
    else:
        print("Workflow State 'Assigned to Vendor' already exists.")

    if not found_assigned:
        print("\nState 'Assigned' not found in Workflow. It might have been already renamed.")
        # Check if 'Assigned to Vendor' already exists
        for state in workflow.states:
            if state.state == 'Assigned to Vendor':
                print("Confirmed: 'Assigned to Vendor' state already exists.")
                return
    
    # 2. Rename 'Assigned' state to 'Assigned to Vendor'
    state_renamed = False
    for state in workflow.states:
        if state.state.strip() == 'Assigned':
            print(f"\nRenaming state '{state.state}' to 'Assigned to Vendor'...")
            state.state = 'Assigned to Vendor'
            state.update_value = 'Assigned to Vendor' # Ensure this matches too
            state_renamed = True
            
    if not state_renamed:
        print("Warning: Could not find 'Assigned' state to rename, even though it seemed to be missing earlier.")

    # 3. Update Transitions
    print("\nUpdating Transitions...")
    transitions_updated = 0
    for transition in workflow.transitions:
        # Check 'state' (From State)
        if transition.state.strip() == 'Assigned':
            print(f"  Updating transition FROM '{transition.state}' -> 'Assigned to Vendor'")
            transition.state = 'Assigned to Vendor'
            transitions_updated += 1
            
        # Check 'next_state' (To State)
        if transition.next_state.strip() == 'Assigned':
            print(f"  Updating transition TO '{transition.next_state}' -> 'Assigned to Vendor'")
            transition.next_state = 'Assigned to Vendor'
            transitions_updated += 1
            
    print(f"Updated {transitions_updated} references in transitions.")

    # 4. Save
    workflow.save()
    frappe.db.commit()
    
    print("\nWorkflow updated successfully!")
    
    # Reload to verify
    workflow.reload()
    print("\nFinal workflow states:")
    for state in workflow.states:
        print(f"  State: '{state.state}' -> Update Value: '{state.update_value}'")

if __name__ == "__main__":
    frappe.init(site='rgespdev.koristu.app')
    frappe.connect()
    rename_workflow_state()
    frappe.destroy()
