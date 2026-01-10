# Copyright (c) 2025, Koristu and contributors
# For license information, please see license.txt

import frappe
from frappe import _


# Item groups that represent selectable components (Panel, Inverter, Battery)
PANEL_GROUPS = ["Panels"]
INVERTER_GROUPS = ["Inverters"]
BATTERY_GROUPS = ["Batteries", "Battery", "Energy Storage"]  # Add variations if needed


def get_item_category(item_code):
    """Get the item_group for an item"""
    return frappe.db.get_value("Item", item_code, "item_group")


def is_panel(item_group):
    return item_group in PANEL_GROUPS


def is_inverter(item_group):
    return item_group in INVERTER_GROUPS


def is_battery(item_group):
    return item_group in BATTERY_GROUPS


def is_selectable_component(item_group):
    """Check if item belongs to Panel/Inverter/Battery categories"""
    return is_panel(item_group) or is_inverter(item_group) or is_battery(item_group)


@frappe.whitelist()
def get_bom_payload(proposed_system_item_code):
    """
    Get BOM data for the proposed system item.
    Returns panel/inverter/battery candidates, quantities, and other items.
    
    Args:
        proposed_system_item_code: Item code of the proposed system (Product)
    
    Returns:
        dict with bom info, candidates, qty_summary, and other_items
    """
    if not proposed_system_item_code:
        return {"error": _("No proposed system specified")}
    
    # Find active BOM for the proposed system
    bom = find_active_bom(proposed_system_item_code)
    
    if not bom:
        return {
            "error": _("No active BOM found for {0}").format(proposed_system_item_code),
            "bom": None
        }
    
    # Get BOM items with their item groups
    bom_items = frappe.db.sql("""
        SELECT 
            bi.item_code, 
            bi.item_name,
            bi.qty, 
            bi.uom,
            bi.description,
            i.item_group,
            bi.idx
        FROM `tabBOM Item` bi
        JOIN `tabItem` i ON bi.item_code = i.name
        WHERE bi.parent = %s
        ORDER BY bi.idx
    """, bom, as_dict=True)
    
    # Categorize items
    panel_candidates = []
    inverter_candidates = []
    battery_candidates = []
    other_items = []
    
    panel_qty_total = 0
    inverter_qty_total = 0
    battery_qty_total = 0
    
    for item in bom_items:
        item_group = item.get("item_group")
        qty = item.get("qty", 0)
        
        if is_panel(item_group):
            panel_candidates.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": qty,
                "uom": item.uom
            })
            panel_qty_total += qty
            
        elif is_inverter(item_group):
            inverter_candidates.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": qty,
                "uom": item.uom
            })
            inverter_qty_total += qty
            
        elif is_battery(item_group):
            battery_candidates.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": qty,
                "uom": item.uom
            })
            battery_qty_total += qty
            
        else:
            # Other items for the editable table
            other_items.append({
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": qty,
                "uom": item.uom,
                "description": item.description or ""
            })
    
    # Determine default selections (if exactly one candidate exists)
    default_selected_panel = panel_candidates[0]["item_code"] if len(panel_candidates) == 1 else ""
    default_selected_inverter = inverter_candidates[0]["item_code"] if len(inverter_candidates) == 1 else ""
    default_selected_battery = battery_candidates[0]["item_code"] if len(battery_candidates) == 1 else ""
    
    return {
        "bom": bom,
        "panel_candidates": panel_candidates,
        "inverter_candidates": inverter_candidates,
        "battery_candidates": battery_candidates,
        "default_selected_panel": default_selected_panel,
        "default_selected_inverter": default_selected_inverter,
        "default_selected_battery": default_selected_battery,
        "qty_summary": {
            "panel_qty_from_bom": panel_qty_total,
            "inverter_qty_from_bom": inverter_qty_total,
            "battery_qty_from_bom": battery_qty_total
        },
        "other_items": other_items
    }


def find_active_bom(item_code):
    """
    Find the active BOM for an item.
    Priority: default active BOM > latest active BOM by modified date
    
    Args:
        item_code: Item code to find BOM for
    
    Returns:
        BOM name or None
    """
    # First try to find default active BOM
    default_bom = frappe.db.get_value(
        "BOM",
        {"item": item_code, "is_active": 1, "is_default": 1},
        "name"
    )
    
    if default_bom:
        return default_bom
    
    # Fallback to latest active BOM
    latest_bom = frappe.db.get_value(
        "BOM",
        {"item": item_code, "is_active": 1},
        "name",
        order_by="modified desc"
    )
    
    return latest_bom


@frappe.whitelist()
def create_technical_survey_from_lead(lead_name):
    """
    Create a Technical Survey from Lead.
    Validates proposed_system is set and copies relevant fields.
    
    Args:
        lead_name: Name of the Lead document
    
    Returns:
        dict with doctype and docname of created Technical Survey
    """
    if not lead_name:
        frappe.throw(_("Lead name is required"))
    
    lead = frappe.get_doc("Lead", lead_name)
    
    # Validate proposed_system is set
    proposed_system = lead.get("custom_proposed_system")
    if not proposed_system:
        frappe.throw(_("Please select a Proposed System (kW / Tier) before creating a Technical Survey"))
    
    # Check if Technical Survey already exists for this Lead
    existing = frappe.db.exists("Technical Survey", {"lead": lead_name})
    if existing:
        return {
            "doctype": "Technical Survey",
            "name": existing,
            "message": _("Technical Survey already exists for this Lead")
        }
    
    # Create Technical Survey
    tech_survey = frappe.get_doc({
        "doctype": "Technical Survey",
        "lead": lead_name,
        "proposed_system": proposed_system,
        # Copy customer information
        "customer_name": lead.get("company_name") or f"{lead.get(first_name, )} {lead.get(last_name, )}".strip(),
        "mobile_no": lead.get("mobile_no"),
        "customer_mobile": lead.get("mobile_no"),
        "customer_email": lead.get("email_id"),
        # Copy address
        "city": lead.get("custom_city") or lead.get("city"),
        "customer_address": get_lead_address(lead),
        # Copy K-Number
        "k_number": lead.get("custom_k_number"),
        # Copy coordinates
        "latitude": lead.get("custom_latitude"),
        "longitude": lead.get("custom_longitude"),
        "google_map_link": lead.get("custom_google_map_link"),
        # Copy electrical details
        "phase_type": lead.get("custom_phase_type"),
        "existing_load_kw": lead.get("custom_existing_load_kw"),
        "required_load_kw": lead.get("custom_required_load_kw"),
        "current_monthly_bill": lead.get("custom_current_monthly_bill"),
        # Copy site details
        "site_type": lead.get("custom_site_type"),
        "roof_type": lead.get("custom_roof_type"),
        "roof_area_sqft": lead.get("custom_roof_area_sqft"),
        "number_of_floors": lead.get("custom_number_of_floors"),
        "area_suitability": lead.get("custom_area_suitability"),
        "direction_shading_remarks": lead.get("custom_direction_shading_remarks") or lead.get("direction_shading_remarks"),
        # Set initial status
        "survey_status": "Pending"
    })
    
    tech_survey.insert(ignore_permissions=True)
    
    # Mark site visit created on Lead
    frappe.db.set_value("Lead", lead_name, "custom_site_visit_created", 1, update_modified=False)
    
    frappe.db.commit()
    
    return {
        "doctype": "Technical Survey",
        "name": tech_survey.name,
        "message": _("Technical Survey created successfully")
    }


def get_lead_address(lead):
    """Combine address fields from Lead"""
    parts = []
    for field in ["custom_address_line_1", "custom_address_line_2", "custom_address_line_3"]:
        value = lead.get(field)
        if value:
            parts.append(value)
    return ", ".join(parts) if parts else ""


@frappe.whitelist()
def validate_lead_for_initiate_job(lead_name):
    """
    Validate that Lead has proposed_system set before Initiate Job
    
    Args:
        lead_name: Lead document name
    
    Returns:
        dict with validation result
    """
    proposed_system = frappe.db.get_value("Lead", lead_name, "custom_proposed_system")
    
    if not proposed_system:
        return {
            "valid": False,
            "message": _("Please select a Proposed System (kW / Tier) before initiating the job.")
        }
    
    return {"valid": True}
