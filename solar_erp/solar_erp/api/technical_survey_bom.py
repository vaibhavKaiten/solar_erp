# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _


@frappe.whitelist()
def get_bom_payload(proposed_system_item_code):
    """
    Get BOM payload for the proposed system item.
    Returns structure with panel/inverter candidates, quantities, and other items.
    
    Args:
        proposed_system_item_code: Item code of the proposed system
        
    Returns:
        dict: {
            bom: BOM name,
            panel_candidates: [{item_code, item_name}],
            inverter_candidates: [{item_code, item_name}],
            default_selected_panel: str or None,
            default_selected_inverter: str or None,
            qty_summary: {panel_qty_from_bom, inverter_qty_from_bom},
            other_items: [{item_code, item_name, qty, uom, description}]
        }
    """
    if not proposed_system_item_code:
        return {"error": "No proposed system provided"}
    
    # Find BOM for the proposed system
    bom = find_active_bom(proposed_system_item_code)
    
    if not bom:
        return {"error": f"No active BOM found for item {proposed_system_item_code}"}
    
    # Get BOM items
    bom_doc = frappe.get_doc("BOM", bom)
    
    # Categorize items
    panel_items = []
    inverter_items = []
    battery_items = []
    other_items = []
    all_items = []  # All items with item_group for client-side storage
    
    panel_qty_sum = 0
    inverter_qty_sum = 0
    battery_qty_sum = 0
    
    for item in bom_doc.items:
        item_doc = frappe.get_cached_doc("Item", item.item_code)
        item_group = item_doc.item_group
        
        item_data = {
            "item_code": item.item_code,
            "item_name": item_doc.item_name,
            "item_group": item_group,  # Include item_group!
            "qty": item.qty,
            "uom": item.uom,
            "description": item_doc.description or ""
        }
        
        all_items.append(item_data)
        
        if item_group == "Panels":
            panel_items.append(item_data)
            panel_qty_sum += item.qty
        elif item_group == "Inverters":
            inverter_items.append(item_data)
            inverter_qty_sum += item.qty
        elif item_group == "Battery":
            battery_items.append(item_data)
            battery_qty_sum += item.qty
        else:
            other_items.append(item_data)
    
    # Determine default selections
    default_panel = panel_items[0]["item_code"] if len(panel_items) == 1 else None
    default_inverter = inverter_items[0]["item_code"] if len(inverter_items) == 1 else None
    default_battery = battery_items[0]["item_code"] if len(battery_items) == 1 else None
    
    return {
        "bom": bom,
        "all_items": all_items,  # All BOM items with item_group
        "panel_candidates": [{k: v for k, v in x.items()} for x in panel_items],
        "inverter_candidates": [{k: v for k, v in x.items()} for x in inverter_items],
        "battery_candidates": [{k: v for k, v in x.items()} for x in battery_items],
        "default_selected_panel": default_panel,
        "default_selected_inverter": default_inverter,
        "default_selected_battery": default_battery,
        "qty_summary": {
            "panel_qty_from_bom": panel_qty_sum,
            "inverter_qty_from_bom": inverter_qty_sum,
            "battery_qty_from_bom": battery_qty_sum
        },
        "other_items": other_items
    }


def find_active_bom(item_code):
    """
    Find the active BOM for an item.
    Prefers submitted & default active BOM, falls back to any submitted active BOM, 
    then falls back to draft BOMs.
    
    Args:
        item_code: Item code
        
    Returns:
        str: BOM name or None
    """
    # Try to find submitted default active BOM
    default_bom = frappe.db.get_value(
        "BOM",
        filters={
            "item": item_code,
            "is_active": 1,
            "is_default": 1,
            "docstatus": 1
        },
        fieldname="name"
    )
    
    if default_bom:
        return default_bom
    
    # Fallback to any submitted active BOM
    submitted_bom = frappe.db.get_all(
        "BOM",
        filters={
            "item": item_code,
            "is_active": 1,
            "docstatus": 1
        },
        fields=["name"],
        order_by="modified desc",
        limit=1
    )
    
    if submitted_bom:
        return submitted_bom[0].name
    
    # Fallback to draft BOMs (for development/testing)
    draft_bom = frappe.db.get_all(
        "BOM",
        filters={
            "item": item_code,
            "is_active": 1,
            "docstatus": 0
        },
        fields=["name"],
        order_by="modified desc",
        limit=1
    )
    
    return draft_bom[0].name if draft_bom else None


@frappe.whitelist()
def get_bom_items_for_dropdown(doctype, txt, searchfield, start, page_len, filters):
    """
    Query function for dropdown to filter items from BOM.
    This approach hides the 'Filters applied for' message.
    """
    allowed_items = filters.get('allowed_items', [])
    
    if not allowed_items:
        return []
    
    # Convert to tuple for SQL IN clause
    allowed_items_str = ", ".join([frappe.db.escape(item) for item in allowed_items])
    
    return frappe.db.sql(f"""
        SELECT name, item_name
        FROM `tabItem`
        WHERE name IN ({allowed_items_str})
        AND (name LIKE %(txt)s OR item_name LIKE %(txt)s)
        ORDER BY name
        LIMIT %(start)s, %(page_len)s
    """, {
        'txt': f'%{txt}%',
        'start': start,
        'page_len': page_len
    })
