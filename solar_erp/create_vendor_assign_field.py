"""
Create vendor_assign field on Lead doctype
"""
import frappe

def create_vendor_assign_field():
    """Create vendor_assign custom field on Lead"""
    
    print("\n" + "="*80)
    print("CREATING VENDOR_ASSIGN FIELD ON LEAD")
    print("="*80 + "\n")
    
    # Check if field already exists
    if frappe.db.exists("Custom Field", "Lead-vendor_assign"):
        print("⚠️  Field 'vendor_assign' already exists on Lead")
        print("Updating existing field...\n")
        field = frappe.get_doc("Custom Field", "Lead-vendor_assign")
    else:
        print("Creating new field 'vendor_assign' on Lead...\n")
        field = frappe.new_doc("Custom Field")
        field.dt = "Lead"
        field.fieldname = "vendor_assign"
    
    # Set field properties
    field.label = "Vendor Assign"
    field.fieldtype = "Link"
    field.options = "Supplier"
    field.insert_after = "territory"
    field.depends_on = "eval:doc.territory || doc.custom_territory_display"
    field.description = "Select Vendor Company for this Territory"
    field.in_standard_filter = 1
    
    # Save the field
    if field.is_new():
        field.insert()
    else:
        field.save()
    
    frappe.db.commit()
    
    print("✅ Field created successfully!")
    print(f"\nField Details:")
    print(f"  Fieldname: {field.fieldname}")
    print(f"  Label: {field.label}")
    print(f"  Type: {field.fieldtype}")
    print(f"  Options: {field.options}")
    print(f"  Insert After: {field.insert_after}")
    print(f"  Depends On: {field.depends_on}")
    
    # Clear cache and reload
    print("\n🔄 Clearing cache...")
    frappe.clear_cache()
    
    print("🔄 Reloading Lead doctype...")
    frappe.reload_doctype("Lead", force=True)
    
    print("\n" + "="*80)
    print("✅ FIELD CREATION COMPLETE")
    print("="*80)
    print("\nNext Steps:")
    print("1. Hard refresh browser (Ctrl+Shift+R)")
    print("2. Open Lead form")
    print("3. Select Territory")
    print("4. vendor_assign field should appear with Supplier dropdown")
    print("="*80 + "\n")

if __name__ == "__main__":
    create_vendor_assign_field()
