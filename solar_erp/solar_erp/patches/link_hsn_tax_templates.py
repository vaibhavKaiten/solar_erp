# Copyright (c) 2025, KaitenSoftware
# Link Item Tax Templates to GST HSN Codes
# Run: bench --site rgespdev.koristu.app execute solar_erp.solar_erp.link_hsn_tax_templates.execute

import frappe

def execute():
    hsn_template_map = {
        "8541": "GST 5% - RGES",
        "8504": "GST 5% - RGES",
        "8507": "GST 18% - RGES",
    }
    default_template = "GST 18% - RGES"
    
    hsn_with_items = frappe.db.sql("""
        SELECT DISTINCT gst_hsn_code 
        FROM tabItem 
        WHERE gst_hsn_code IS NOT NULL AND gst_hsn_code != ''
    """, as_dict=True)
    
    print(f"Found {len(hsn_with_items)} HSN codes with items")
    updated = 0
    
    for row in hsn_with_items:
        hsn_code = row.gst_hsn_code
        if not hsn_code:
            continue
            
        prefix = hsn_code[:4] if len(hsn_code) >= 4 else hsn_code
        template_name = hsn_template_map.get(prefix, default_template)
        
        if not frappe.db.exists("GST HSN Code", {"hsn_code": hsn_code}):
            print(f"HSN {hsn_code} not in GST HSN Code table, skipping")
            continue
        
        hsn_doc = frappe.get_doc("GST HSN Code", {"hsn_code": hsn_code})
        
        has_template = False
        for tax in hsn_doc.taxes:
            if tax.item_tax_template == template_name:
                has_template = True
                break
        
        if not has_template:
            hsn_doc.append("taxes", {"item_tax_template": template_name})
            hsn_doc.flags.ignore_permissions = True
            hsn_doc.save()
            rate = "5%" if "5%" in template_name else "18%"
            print(f"Added {rate} template to HSN {hsn_code}")
            updated += 1
    
    frappe.db.commit()
    print(f"\nUpdated {updated} HSN codes with tax templates")
