# -*- coding: utf-8 -*-
# Copyright (c) 2025, Solar ERP
# For license information, please see license.txt

import frappe
from frappe import _


def on_submit(doc, method):
    """
    Called when Delivery Note is submitted.
    Auto-creates Structure Mounting to start the execution pipeline.
    """
    # First, let existing stock reservation logic run
    from solar_erp.solar_erp.api.bom_stock_reservation import on_delivery_submit
    on_delivery_submit(doc, method)
    
    # Then auto-create Structure Mounting
    auto_create_structure_mounting(doc)


def auto_create_structure_mounting(delivery_note):
    """
    Automatically creates Structure Mounting when Delivery Note is submitted.
    
    Rules:
    - Only creates if linked to a Sales Order
    - Only creates ONE Structure Mounting per Sales Order
    - No duplicates even on re-submission or amendment
    """
    # Get linked Sales Order(s)
    sales_orders = set()
    for item in delivery_note.items:
        if item.against_sales_order:
            sales_orders.add(item.against_sales_order)
    
    if not sales_orders:
        frappe.log_error(
            title=_("No Sales Order linked to Delivery Note"),
            message=f"Delivery Note {delivery_note.name} has no linked Sales Order. Structure Mounting not created."
        )
        return
    
    # Process each Sales Order
    for sales_order_name in sales_orders:
        try:
            create_structure_mounting_for_sales_order(sales_order_name, delivery_note.name)
        except Exception as e:
            frappe.log_error(
                title=_("Structure Mounting Auto-Creation Failed"),
                message=f"Failed to create Structure Mounting for SO {sales_order_name}: {str(e)}\n\n{frappe.get_traceback()}"
            )


def create_structure_mounting_for_sales_order(sales_order_name, delivery_note_name):
    """
    Creates a Structure Mounting document for the given Sales Order.
    
    Duplicate Prevention:
    - Checks if Structure Mounting already exists for this Sales Order
    - If exists, does nothing
    """
    # Check if Structure Mounting already exists for this Sales Order
    existing = frappe.db.exists("Structure Mounting", {
        "sales_order": sales_order_name,
        "docstatus": ["<", 2]  # Not cancelled
    })
    
    if existing:
        frappe.msgprint(
            _("Structure Mounting {0} already exists for Sales Order {1}. Skipping creation.").format(
                existing, sales_order_name
            ),
            alert=True
        )
        return
    
    # Get Sales Order details
    sales_order = frappe.get_doc("Sales Order", sales_order_name)
    
    # Try to find Lead through multiple paths
    lead = None
    technical_survey = None
    job_file = None
    
    # Path 1: Check if Sales Order has prevdoc (Quotation)
    if sales_order.items and sales_order.items[0].prevdoc_docname:
        quotation_name = sales_order.items[0].prevdoc_docname
        quotation = frappe.get_doc("Quotation", quotation_name)
        
        if quotation.quotation_to == "Lead" and quotation.party_name:
            lead = quotation.party_name
    
    # Path 2: Check Technical Survey linked to this SO or Customer
    if not lead:
        # Try to find Technical Survey by customer
        ts_list = frappe.get_all("Technical Survey",
            filters={
                "customer": sales_order.customer,
                "docstatus": ["<", 2]
            },
            fields=["name", "lead"],
            order_by="creation desc",
            limit=1
        )
        if ts_list and ts_list[0].lead:
            lead = ts_list[0].lead
            technical_survey = frappe.get_doc("Technical Survey", ts_list[0].name)
    
    # Path 3: Try to find through Job File/Project
    if sales_order.project:
        job_file = sales_order.project
        
        if not lead:
            # Try to find lead from Job File
            jf = frappe.get_doc("Job File", job_file)
            if hasattr(jf, 'lead') and jf.lead:
                lead = jf.lead
    
    # Get vendor executive from Technical Survey
    assigned_vendor = None
    assigned_internal_user = None
    
    if technical_survey:
        assigned_vendor = technical_survey.get("assigned_vendor")
        assigned_internal_user = technical_survey.get("assigned_vendor_executive")
    elif lead:
        # Try to get from Technical Survey by lead
        ts = frappe.db.get_value("Technical Survey",
            {"lead": lead, "docstatus": ["<", 2]},
            ["assigned_vendor", "assigned_vendor_executive"],
            as_dict=True,
            order_by="creation desc"
        )
        if ts:
            assigned_vendor = ts.get("assigned_vendor")
            assigned_internal_user = ts.get("assigned_vendor_executive")
    
    # Create Structure Mounting document
    structure_mounting = frappe.new_doc("Structure Mounting")
    
    # Set references (lead can be None if not found)
    structure_mounting.lead = lead
    structure_mounting.sales_order = sales_order_name
    structure_mounting.job_file = job_file
    structure_mounting.customer = sales_order.customer
    structure_mounting.delivery_note = delivery_note_name
    
    # Set assignment (validate before assigning)
    if assigned_vendor and frappe.db.exists("Supplier", assigned_vendor):
        structure_mounting.assigned_vendor = assigned_vendor
    if assigned_internal_user and frappe.db.exists("User", assigned_internal_user):
        structure_mounting.assigned_internal_user = assigned_internal_user
    
    # Set default status
    structure_mounting.status = "Draft"
    
    # Set planned dates (optional - can be updated later)
    if technical_survey and technical_survey.get("planned_start_date"):
        structure_mounting.planned_start_date = technical_survey.planned_start_date
    
    # Set flag to allow auto-creation (bypass manual creation validation)
    frappe.local.auto_creating_structure_mounting = True
    
    # Insert the document (stays in Draft)
    structure_mounting.insert(ignore_permissions=True)
    
    # Clear the flag
    frappe.local.auto_creating_structure_mounting = False
    
    frappe.msgprint(
        _("Structure Mounting {0} created successfully for Sales Order {1}").format(
            structure_mounting.name, sales_order_name
        ),
        alert=True,
        indicator="green"
    )
    
    frappe.logger().info(f"Structure Mounting {structure_mounting.name} auto-created for SO {sales_order_name}")
