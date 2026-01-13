#!/usr/bin/env python3
"""
Fix Technical Survey Workflow - Remove trailing space from 'Assigned' status
"""
import frappe

def fix_workflow_status():
    """Fix the Technical Survey workflow state 'Assigned' which has a trailing space"""
    
    # Get the workflow
    workflow = frappe.get_doc('Workflow', 'Technical Survey')
    
    print("Current workflow states:")
    for state in workflow.states:
        print(f"  State: '{state.state}' -> Update Value: '{state.update_value}'")
    
    # Find and fix the 'Assigned' state
    for state in workflow.states:
        if state.state == 'Assigned':
            old_value = state.update_value
            # Remove trailing/leading spaces and set to "Assigned to Vendor"
            state.update_value = 'Assigned to Vendor'
            print(f"\nFixed state '{state.state}':")
            print(f"  Old update_value: '{old_value}'")
            print(f"  New update_value: '{state.update_value}'")
    
    # Save the workflow
    workflow.save()
    frappe.db.commit()
    
    print("\nWorkflow updated successfully!")
    print("\nUpdated workflow states:")
    for state in workflow.states:
        print(f"  State: '{state.state}' -> Update Value: '{state.update_value}'")

if __name__ == "__main__":
    frappe.init(site='rgespdev.koristu.app')
    frappe.connect()
    fix_workflow_status()
    frappe.destroy()
