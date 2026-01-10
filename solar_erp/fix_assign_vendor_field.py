"""
Force update assign_vendor field to ensure it shows Suppliers
"""
import frappe

def fix_assign_vendor_field():
    """Update assign_vendor field to Link to Supplier"""
    
    print("\n" + "="*80)
    print("FIXING ASSIGN_VENDOR FIELD ON LEAD")
    print("="*80 + "\n")
    
    # Get the Custom Field
    field_name = "Lead-assign_vendor"
    
    if not frappe.db.exists("Custom Field", field_name):
        print(f"❌ Custom Field {field_name} not found!")
        return
    
    # Update the field
    field = frappe.get_doc("Custom Field", field_name)
    
    print(f"Current configuration:")
    print(f"  Fieldname: {field.fieldname}")
    print(f"  Field Type: {field.fieldtype}")
    print(f"  Options: {field.options}")
    print(f"  Insert After: {field.insert_after}")
    
    # Force update to Supplier
    changed = False
    
    if field.options != "Supplier":
        print(f"\n⚠️  Options is '{field.options}', changing to 'Supplier'")
        field.options = "Supplier"
        changed = True
    
    if field.insert_after != "territory":
        print(f"\n⚠️  Insert After is '{field.insert_after}', changing to 'territory'")
        field.insert_after = "territory"
        changed = True
    
    if changed:
        field.save()
        frappe.db.commit()
        print("\n✅ Field updated successfully!")
    else:
        print("\n✅ Field is already correctly configured")
    
    # Clear cache
    print("\n🔄 Clearing cache...")
    frappe.clear_cache()
    
    # Reload doctype
    print("🔄 Reloading Lead doctype...")
    frappe.reload_doctype("Lead", force=True)
    
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    
    # Verify the change
    field.reload()
    print(f"\nUpdated configuration:")
    print(f"  Fieldname: {field.fieldname}")
    print(f"  Field Type: {field.fieldtype}")
    print(f"  Options: {field.options}")
    print(f"  Insert After: {field.insert_after}")
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("1. Hard refresh your browser (Ctrl+Shift+R or Cmd+Shift+R)")
    print("2. Open a Lead form")
    print("3. Select Territory")
    print("4. Check assign_vendor dropdown - should show Suppliers only")
    print("="*80 + "\n")

if __name__ == "__main__":
    fix_assign_vendor_field()
