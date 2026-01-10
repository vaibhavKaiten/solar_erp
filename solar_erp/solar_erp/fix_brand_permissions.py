"""
Script to check items and fix brand permissions
Run with: bench --site rgespdev.koristu.app execute solar_erp.solar_erp.fix_brand_permissions.run
"""
import frappe


def run():
    """Check Items and Brands and fix permissions"""
    
    # Check panel items
    print("\n=== Panel Items ===")
    items = frappe.get_all(
        "Item",
        filters=[["item_name", "like", "%panel%"]],
        fields=["name", "item_name", "brand", "item_group"],
        limit=20
    )
    for item in items:
        print(f"  {item.item_name} | Brand: {item.brand} | Group: {item.item_group}")
    
    # Check inverter items
    print("\n=== Inverter Items ===")
    items = frappe.get_all(
        "Item",
        filters=[["item_name", "like", "%inverter%"]],
        fields=["name", "item_name", "brand", "item_group"],
        limit=10
    )
    for item in items:
        print(f"  {item.item_name} | Brand: {item.brand} | Group: {item.item_group}")
    
    # Check brands
    print("\n=== Brands ===")
    brands = frappe.get_all("Brand", fields=["name"], limit=20)
    for brand in brands:
        print(f"  {brand.name}")
    
    # Check Item Groups
    print("\n=== Item Groups ===")
    groups = frappe.get_all("Item Group", filters=[["is_group", "=", 0]], fields=["name"], limit=20)
    for group in groups:
        print(f"  {group.name}")
    
    # Add read permission for Brand to Technical Survey Executive
    print("\n=== Adding Brand Permission ===")
    add_brand_permission()
    
    # Add read permission for Item to Technical Survey Executive
    print("\n=== Adding Item Permission ===")
    add_item_permission()


def add_brand_permission():
    """Add read permission for Brand DocType to Technical Survey Executive"""
    role = "Technical Survey Executive"
    
    # Check if permission already exists
    existing = frappe.db.exists("Custom DocPerm", {
        "parent": "Brand",
        "role": role
    })
    
    if existing:
        print(f"  Brand permission for {role} already exists")
        return
    
    # Add custom permission via DocPerm
    try:
        brand_doc = frappe.get_doc("DocType", "Brand")
        brand_doc.append("permissions", {
            "role": role,
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0
        })
        brand_doc.save(ignore_permissions=True)
        print(f"  Added Brand read permission for {role}")
    except Exception as e:
        print(f"  Error adding Brand permission: {e}")
        # Try using Custom DocPerm
        try:
            frappe.get_doc({
                "doctype": "Custom DocPerm",
                "parent": "Brand",
                "parenttype": "DocType",
                "parentfield": "permissions",
                "role": role,
                "read": 1,
                "write": 0,
                "create": 0,
                "delete": 0
            }).insert(ignore_permissions=True)
            print(f"  Added Brand read permission via Custom DocPerm for {role}")
        except Exception as e2:
            print(f"  Error with Custom DocPerm: {e2}")


def add_item_permission():
    """Add read permission for Item DocType to Technical Survey Executive"""
    role = "Technical Survey Executive"
    
    # Check if role already has Item permission
    has_perm = frappe.db.exists("DocPerm", {
        "parent": "Item",
        "role": role,
        "read": 1
    })
    
    if has_perm:
        print(f"  Item permission for {role} already exists")
        return
    
    try:
        item_doc = frappe.get_doc("DocType", "Item")
        item_doc.append("permissions", {
            "role": role,
            "read": 1,
            "write": 0,
            "create": 0,
            "delete": 0,
            "select": 1
        })
        item_doc.save(ignore_permissions=True)
        print(f"  Added Item read permission for {role}")
    except Exception as e:
        print(f"  Error adding Item permission: {e}")


if __name__ == "__main__":
    run()
