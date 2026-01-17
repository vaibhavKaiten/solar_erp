# Copyright (c) 2025, KaitenSoftware
# Assign GST Templates to Items
# Run: bench --site rgespdev.koristu.app execute solar_erp.solar_erp.assign_gst_templates.execute

import frappe

def execute():
    template_5 = "GST 5% - RGES"
    template_18 = "GST 18% - RGES"
    
    items = frappe.get_all("Item", filters={"disabled": 0}, fields=["name", "item_name", "item_group"])
    assigned_5 = 0
    assigned_18 = 0
    
    for item in items:
        item_doc = frappe.get_doc("Item", item.name)
        item_name_lower = (item.item_name or "").lower()
        item_group_lower = (item.item_group or "").lower()
        
        if item_doc.taxes and len(item_doc.taxes) > 0:
            existing = item_doc.taxes[0].item_tax_template
            if existing in [template_5, template_18]:
                continue
        
        is_panel_inverter = False
        if "panel" in item_name_lower or "panel" in item_group_lower:
            is_panel_inverter = True
        elif "inverter" in item_name_lower or "inverter" in item_group_lower:
            is_panel_inverter = True
        elif "pv module" in item_name_lower:
            is_panel_inverter = True
        
        template_to_use = template_5 if is_panel_inverter else template_18
        
        item_doc.taxes = []
        item_doc.append("taxes", {"item_tax_template": template_to_use})
        item_doc.flags.ignore_permissions = True
        item_doc.save()
        
        if is_panel_inverter:
            assigned_5 += 1
            print(f"5% -> {item.name}")
        else:
            assigned_18 += 1
            print(f"18% -> {item.name}")
    
    frappe.db.commit()
    print(f"\nAssigned GST 5%: {assigned_5} items (Panels/Inverters)")
    print(f"Assigned GST 18%: {assigned_18} items (Other)")
    print("Done!")
