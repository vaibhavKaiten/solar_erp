# Copyright (c) 2025, KaitenSoftware
# GST Configuration Script for Purchase Orders
# 
# This script sets up:
# 1. Item Tax Templates for 5% and 18% GST
# 2. Assigns templates to appropriate Item Groups
# 3. Verifies Purchase Tax Templates exist
#
# Usage: Run via bench console
# cd ~/Solar_Erp && bench --site rgespdev.koristu.app console < apps/solar_erp/solar_erp/solar_erp/setup_purchase_gst.py

import frappe
from frappe import _


def execute():
    """Main execution function"""
    print("=" * 60)
    print("GST Configuration for Purchase Orders")
    print("=" * 60)
    
    # Get company
    company = get_company()
    if not company:
        print("ERROR: No company found!")
        return
    
    print(f"\nCompany: {company}")
    
    # Step 1: Get GST Account heads
    gst_accounts = get_gst_accounts(company)
    print(f"\nGST Accounts found:")
    for key, value in gst_accounts.items():
        print(f"  {key}: {value}")
    
    # Step 2: Create/Update Item Tax Templates
    create_item_tax_templates(company, gst_accounts)
    
    # Step 3: Verify Purchase Taxes & Charges Templates
    verify_purchase_tax_templates(company, gst_accounts)
    
    # Step 4: Assign Item Tax Templates to Item Groups
    assign_templates_to_item_groups(company)
    
    frappe.db.commit()
    print("\n" + "=" * 60)
    print("GST Configuration Complete!")
    print("=" * 60)


def get_company():
    """Get the main company"""
    company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not company:
        companies = frappe.get_all("Company", limit=1)
        if companies:
            company = companies[0].name
    return company


def get_gst_accounts(company):
    """Get GST account heads for the company"""
    accounts = {}
    
    # Input Tax accounts (for purchases)
    accounts["input_cgst"] = frappe.db.get_value(
        "Account", 
        {"account_name": "Input Tax CGST", "company": company},
        "name"
    ) or f"Input Tax CGST - {company[:4]}"
    
    accounts["input_sgst"] = frappe.db.get_value(
        "Account", 
        {"account_name": "Input Tax SGST", "company": company},
        "name"
    ) or f"Input Tax SGST - {company[:4]}"
    
    accounts["input_igst"] = frappe.db.get_value(
        "Account", 
        {"account_name": "Input Tax IGST", "company": company},
        "name"
    ) or f"Input Tax IGST - {company[:4]}"
    
    return accounts


def create_item_tax_templates(company, gst_accounts):
    """Create Item Tax Templates for 5% and 18% GST"""
    
    print("\n--- Creating Item Tax Templates ---")
    
    # Template 1: GST 5% for Panels & Inverters (Purchase)
    template_5_name = f"GST 5% - Purchase - {company}"
    create_or_update_item_tax_template(
        name=template_5_name,
        company=company,
        taxes=[
            {"tax_type": gst_accounts["input_cgst"], "tax_rate": 2.5},
            {"tax_type": gst_accounts["input_sgst"], "tax_rate": 2.5},
            {"tax_type": gst_accounts["input_igst"], "tax_rate": 5.0},
        ]
    )
    
    # Template 2: GST 18% for Other Items (Purchase)
    template_18_name = f"GST 18% - Purchase - {company}"
    create_or_update_item_tax_template(
        name=template_18_name,
        company=company,
        taxes=[
            {"tax_type": gst_accounts["input_cgst"], "tax_rate": 9.0},
            {"tax_type": gst_accounts["input_sgst"], "tax_rate": 9.0},
            {"tax_type": gst_accounts["input_igst"], "tax_rate": 18.0},
        ]
    )


def create_or_update_item_tax_template(name, company, taxes):
    """Create or update an Item Tax Template"""
    
    if frappe.db.exists("Item Tax Template", name):
        doc = frappe.get_doc("Item Tax Template", name)
        print(f"  Updating: {name}")
    else:
        doc = frappe.new_doc("Item Tax Template")
        doc.name = name
        doc.title = name
        doc.company = company
        print(f"  Creating: {name}")
    
    # Clear existing taxes and add new ones
    doc.taxes = []
    for tax in taxes:
        doc.append("taxes", {
            "tax_type": tax["tax_type"],
            "tax_rate": tax["tax_rate"]
        })
    
    doc.flags.ignore_permissions = True
    doc.save()
    print(f"    ✓ Saved with {len(taxes)} tax rates")


def verify_purchase_tax_templates(company, gst_accounts):
    """Verify Purchase Taxes & Charges Templates exist"""
    
    print("\n--- Verifying Purchase Tax Templates ---")
    
    # Template A: Intra-State (CGST + SGST)
    intra_name = f"Input GST In-state - {company[:4]}"
    if frappe.db.exists("Purchase Taxes and Charges Template", intra_name):
        print(f"  ✓ Found: {intra_name}")
    else:
        create_purchase_tax_template(
            name=intra_name,
            company=company,
            is_intra_state=True,
            gst_accounts=gst_accounts
        )
    
    # Template B: Inter-State (IGST)
    inter_name = f"Input GST Out-state - {company[:4]}"
    if frappe.db.exists("Purchase Taxes and Charges Template", inter_name):
        print(f"  ✓ Found: {inter_name}")
    else:
        create_purchase_tax_template(
            name=inter_name,
            company=company,
            is_intra_state=False,
            gst_accounts=gst_accounts
        )


def create_purchase_tax_template(name, company, is_intra_state, gst_accounts):
    """Create a Purchase Taxes and Charges Template"""
    
    doc = frappe.new_doc("Purchase Taxes and Charges Template")
    doc.name = name
    doc.title = name
    doc.company = company
    doc.is_default = 0
    
    if is_intra_state:
        # CGST + SGST
        doc.append("taxes", {
            "charge_type": "On Net Total",
            "account_head": gst_accounts["input_cgst"],
            "rate": 0,  # Rate comes from Item Tax Template
            "description": "CGST",
            "included_in_print_rate": 0
        })
        doc.append("taxes", {
            "charge_type": "On Net Total",
            "account_head": gst_accounts["input_sgst"],
            "rate": 0,  # Rate comes from Item Tax Template
            "description": "SGST",
            "included_in_print_rate": 0
        })
    else:
        # IGST
        doc.append("taxes", {
            "charge_type": "On Net Total",
            "account_head": gst_accounts["input_igst"],
            "rate": 0,  # Rate comes from Item Tax Template
            "description": "IGST",
            "included_in_print_rate": 0
        })
    
    doc.flags.ignore_permissions = True
    doc.insert()
    print(f"  ✓ Created: {name}")


def assign_templates_to_item_groups(company):
    """Assign Item Tax Templates to relevant Item Groups"""
    
    print("\n--- Assigning Templates to Item Groups ---")
    
    template_5 = f"GST 5% - Purchase - {company}"
    template_18 = f"GST 18% - Purchase - {company}"
    
    # Item Groups for 5% GST (Panels & Inverters)
    groups_5_percent = [
        "Solar Panels",
        "Panels",
        "Panel",
        "Inverters",
        "Inverter",
        "Solar Inverters"
    ]
    
    # Item Groups for 18% GST (Other items)
    groups_18_percent = [
        "Batteries",
        "Battery",
        "Structures",
        "Structure",
        "Mounting Structures",
        "Cables",
        "Cable",
        "BOS",
        "Balance of System",
        "Others",
        "Accessories"
    ]
    
    # Assign 5% template
    for group_name in groups_5_percent:
        if frappe.db.exists("Item Group", group_name):
            assign_item_tax_template_to_group(group_name, template_5, company)
    
    # Assign 18% template
    for group_name in groups_18_percent:
        if frappe.db.exists("Item Group", group_name):
            assign_item_tax_template_to_group(group_name, template_18, company)
    
    print("\n  Note: Also assign templates directly to items if needed.")


def assign_item_tax_template_to_group(group_name, template_name, company):
    """Assign an Item Tax Template to an Item Group"""
    
    # Get all items in this group
    items = frappe.get_all(
        "Item",
        filters={"item_group": group_name, "disabled": 0},
        pluck="name"
    )
    
    if not items:
        print(f"  No items in group: {group_name}")
        return
    
    count = 0
    for item_code in items:
        item = frappe.get_doc("Item", item_code)
        
        # Check if template already assigned
        template_exists = False
        for tax in item.taxes:
            if tax.item_tax_template == template_name:
                template_exists = True
                break
        
        if not template_exists:
            item.append("taxes", {
                "item_tax_template": template_name
            })
            item.flags.ignore_permissions = True
            item.save()
            count += 1
    
    if count > 0:
        print(f"  ✓ Assigned '{template_name}' to {count} items in '{group_name}'")
    else:
        print(f"  ✓ All items in '{group_name}' already have template")


# Additional utility functions for validation

def get_item_gst_rate(item_code):
    """Get the GST rate for an item based on its Item Tax Template"""
    
    item = frappe.get_doc("Item", item_code)
    
    if not item.taxes:
        return None, "No Item Tax Template assigned"
    
    # Get the first applicable template
    template_name = item.taxes[0].item_tax_template
    if not template_name:
        return None, "No Item Tax Template assigned"
    
    template = frappe.get_doc("Item Tax Template", template_name)
    
    # Sum up the rates (for intra-state: CGST + SGST, for inter-state: IGST)
    total_rate = sum(tax.tax_rate for tax in template.taxes if "IGST" in tax.tax_type)
    if total_rate == 0:
        total_rate = sum(tax.tax_rate for tax in template.taxes if "CGST" in tax.tax_type or "SGST" in tax.tax_type)
    
    return total_rate, template_name


def validate_item_gst_setup():
    """Validate that all items have correct GST setup"""
    
    print("\n--- Validating Item GST Setup ---")
    
    items = frappe.get_all(
        "Item",
        filters={"disabled": 0, "is_stock_item": 1},
        fields=["name", "item_name", "item_group"]
    )
    
    missing_template = []
    for item in items:
        rate, template = get_item_gst_rate(item.name)
        if rate is None:
            missing_template.append(f"{item.name} ({item.item_group})")
    
    if missing_template:
        print(f"  WARNING: {len(missing_template)} items without GST templates:")
        for item in missing_template[:10]:
            print(f"    - {item}")
        if len(missing_template) > 10:
            print(f"    ... and {len(missing_template) - 10} more")
    else:
        print("  ✓ All stock items have GST templates assigned")


if __name__ == "__main__":
    execute()
