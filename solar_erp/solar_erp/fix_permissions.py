import frappe

def execute():
    """Fix Custom DocPerm entries that are overriding standard permissions"""
    doctype = "Structure Mounting"
    
    # Delete existing Custom DocPerm for this doctype
    custom_perms = frappe.get_all("Custom DocPerm", 
                                   filters={"parent": doctype}, 
                                   fields=["name", "role", "permlevel"])
    
    print(f"Found {len(custom_perms)} Custom DocPerm entries to delete:")
    for cp in custom_perms:
        print(f"  - Deleting: {cp.name} (Role: {cp.role}, Level: {cp.permlevel})")
        frappe.delete_doc("Custom DocPerm", cp.name, force=True)
    
    frappe.db.commit()
    
    # Clear cache
    frappe.clear_cache(doctype=doctype)
    
    # Reload the doctype to ensure permissions are refreshed
    frappe.reload_doctype(doctype)
    
    print(f"\nCustom DocPerm entries deleted. Permissions should now come from DocType definition.")
    
    # Verify the meta permissions now
    meta = frappe.get_meta(doctype)
    print(f"\n=== Updated Meta Permissions ===")
    for perm in meta.permissions:
        print(f"Role: {perm.role}, Level: {perm.permlevel}, Read: {perm.read}, Write: {perm.write}, Create: {perm.create}")
