import frappe

@frappe.whitelist()
def get_bom_items(item_code):
    """Fetch BOM items for the given item code"""
    
    if not item_code:
        frappe.throw("Item Code is required")
    
    # Get default BOM for the item
    bom = frappe.db.get_value("BOM", {"item": item_code, "is_default": 1}, "name")
    
    if not bom:
        frappe.msgprint(f"No default BOM found for item: {item_code}")
        return []
    
    # Fetch BOM items
    bom_items = frappe.get_all(
        "BOM Item",
        filters={"parent": bom},
        fields=["item_code", "qty", "uom", "description"]
    )
    
    frappe.msgprint(f"Found {len(bom_items)} items in BOM: {bom}")
    
    return bom_items
