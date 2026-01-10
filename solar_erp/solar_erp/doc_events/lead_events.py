# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from solar_erp.solar_erp.api.lead_vendor import validate_vendor_manager_territory
from solar_erp.solar_erp.doc_events.lead_validation import validate_vendors
from solar_erp.solar_erp.api.job import populate_execution_status

def sanitize_vendor_field(doc, fieldname, label):
    """
    Ensure vendor field contains only valid Supplier ID, not email.
    Clears field if it contains invalid data.
    
    Args:
        doc: Lead document
        fieldname: Field name to sanitize
        label: Field label for user messages
    """
    value = doc.get(fieldname)
    if not value:
        return
    
    # Reject email addresses
    if '@' in str(value):
        frappe.msgprint(
            _(f"Warning: {label} contains an email address. Vendor fields must reference Supplier companies only. Clearing invalid value."),
            indicator="orange",
            alert=True
        )
        doc.set(fieldname, None)
        return
    
    # Validate Supplier exists
    if not frappe.db.exists("Supplier", value):
        frappe.msgprint(
            _(f"Warning: {label} '{value}' not found in Supplier list. Clearing invalid value."),
            indicator="orange",
            alert=True
        )
        doc.set(fieldname, None)


def validate(doc, method=None):
    """Lead validate hook - Validate proposed_system and territory before Initiate Job"""
    # Validate Vendor Manager assignment based on Territory
    validate_vendor_manager_territory(doc, method)
    
    # Sync territory fields - PRIORITY ORDER MATTERS!
    # 1. First, sync custom_assignment_territory -> territory (user's current selection)
    if doc.get('custom_assignment_territory'):
        doc.territory = doc.custom_assignment_territory
        doc.custom_territory_display = doc.custom_assignment_territory
    # 2. Then, sync custom_territory_display -> territory (fallback)
    elif doc.get('custom_territory_display'):
        doc.territory = doc.custom_territory_display
        doc.custom_assignment_territory = doc.custom_territory_display
    # 3. Finally, sync territory -> custom fields (backward compatibility)
    elif doc.get('territory'):
        doc.custom_territory_display = doc.territory
        doc.custom_assignment_territory = doc.territory
    
    # Debug logging
    frappe.logger().debug(f"Lead validate: workflow_state={doc.workflow_state}, territory={doc.territory}, custom_territory_display={doc.get('custom_territory_display')}")
    
    # Check for Initiate Job state - use both old and new workflow state
    is_initiating = (
        doc.workflow_state == 'Initiate Job' or
        doc.has_value_changed('workflow_state') and doc.workflow_state == 'Initiate Job'
    )
    
    if is_initiating:
        if not doc.get('custom_proposed_system'):
            frappe.throw(_('Please select a Proposed System (kW / Tier) before initiating the job.'), title=_('Proposed System Required'))
        
        # Check territory - look at all possible field names and database values as fallback
        territory = (
            doc.get('custom_assignment_territory') or 
            doc.get('custom_territory_display') or 
            doc.get('territory')
        )
        
        # Only query database if document is saved and field exists
        if not territory and doc.name:
            try:
                # Try new field first (might not exist in database yet)
                territory = frappe.db.get_value('Lead', doc.name, 'custom_assignment_territory')
            except Exception:
                pass  # Field doesn't exist in database yet, skip
            
            if not territory:
                try:
                    territory = frappe.db.get_value('Lead', doc.name, 'territory')
                except Exception:
                    pass
            
            if not territory:
                try:
                    territory = frappe.db.get_value('Lead', doc.name, 'custom_territory_display')
                except Exception:
                    pass
        
        if not territory:
            frappe.throw(
                _('Please set the Assignment Territory (in Territory & Assignment section) and SAVE the Lead before initiating the job.'), 
                title=_('Territory Required')
            )
    # Sanitize vendor fields before validation (including old assign_vendor field)
    sanitize_vendor_field(doc, "assign_vendor", "Assigned Vendor (Legacy)")
    sanitize_vendor_field(doc, "vendor_assign", "Technical Execution Vendor")
    sanitize_vendor_field(doc, "meter_execution_vendor", "Meter Execution Vendor")
    
    # Validate vendors for technical execution and meter execution
    validate_vendors(doc)


def on_update(doc, method=None):
    """
    
    Lead on_update hook - Auto-create Job File when Lead workflow_state changes to 'Initiate Job'
    Also syncs status field with workflow_state to prevent Frappe from overriding it
    Also auto-creates Customer when status becomes 'Qualified'
    """
    
    # CRITICAL: Sync status with workflow_state to prevent Frappe's core logic from overriding
    # The workflow uses workflow_state, but Frappe's core sets status to "Opportunity" automatically
    # We need to keep them in sync
    if doc.workflow_state and doc.status != doc.workflow_state:
        # Map workflow_state to status
        # This ensures the status field reflects the actual workflow state
        doc.db_set("status", doc.workflow_state, update_modified=False)
        frappe.logger().debug(f"Lead {doc.name}: Synced status from '{doc.status}' to '{doc.workflow_state}'")
    
    # Check if workflow_state field has changed using has_value_changed
    if doc.has_value_changed("workflow_state"):
        new_workflow_state = doc.workflow_state
        
        # Check if changed TO "Initiate Job"
        if new_workflow_state == "Initiate Job":
            create_job_file_from_lead(doc)
    
    # Status-based automation for Customer creation
    # Note: We check workflow_state instead of status since they should be synced
    if doc.has_value_changed("workflow_state"):
        new_workflow_state = doc.workflow_state
        
        # Auto-create Customer when workflow_state becomes "Qualified"
        if new_workflow_state == "Qualified":
            auto_create_customer_on_qualified(doc)



def get_valid_supplier(vendor, field_label):
    if not vendor:
        return None

    # Block emails
    if "@" in vendor:
        frappe.throw(
            _(f"{field_label} must be a Supplier, not an email: {vendor}")
        )

    # Must exist as Supplier
    if not frappe.db.exists("Supplier", vendor):
        frappe.throw(
            _(f"Supplier '{vendor}' does not exist. Please select a valid Supplier.")
        )

    return vendor


@frappe.whitelist()
def create_job_file_from_lead(lead_name):
    # Accept both Lead document object and lead name string
    if isinstance(lead_name, str):
        lead = frappe.get_doc("Lead", lead_name)
    else:
        # lead_name is actually a Lead document object
        lead = lead_name

    # 1. Validate required fields
    if not lead.territory:
        frappe.throw(_("Territory is required"))

    if not lead.vendor_assign:
        frappe.throw(_("Technical Execution Vendor is required"))

    if not lead.meter_execution_vendor:
        frappe.throw(_("Meter Execution Vendor is required"))

    # 2. Create Job File (only one)
    job_file = frappe.get_doc({
        "doctype": "Job File",
        "lead": lead.name,
        "customer": lead.customer,
        "overall_status": "Open"
    })
    job_file.insert(ignore_permissions=True)
    populate_execution_status(job_file, lead)
    job_file.save(ignore_permissions=True)
    # 3. Technical vendor executions
    create_execution("Technical Survey", job_file, lead, lead.vendor_assign)
    create_execution("Structure Mounting", job_file, lead, lead.vendor_assign)
    create_execution("Project Installation", job_file, lead, lead.vendor_assign)
    create_execution("Verification Handover", job_file, lead, lead.vendor_assign)

    # 4. Meter vendor executions
    create_execution("Meter Installation", job_file, lead, lead.meter_execution_vendor)
    create_execution("Meter Commissioning", job_file, lead, lead.meter_execution_vendor)

    # 5. Link back
    lead.custom_job_file = job_file.name
    lead.save(ignore_permissions=True)
    
    # 6. Show success message
    frappe.msgprint(
        _("Job File {0} created successfully!<br><br>"
          "📋 Created Documents:<br>"
          "• Technical Survey<br>"
          "• Structure Mounting<br>"
          "• Project Installation<br>"
          "• Meter Installation<br>"
          "• Meter Commissioning<br>"
          "• Verification Handover<br><br>"
          "All documents are in <b>Draft</b> status with vendors assigned.").format(
            frappe.get_desk_link("Job File", job_file.name)
        ),
        title=_("Job Initiated Successfully"),
        indicator="green",
        alert=True
    )

    return job_file.name


def create_execution(doctype, job_file, lead, vendor, field_label="Assigned Vendor"):
    valid_vendor = get_valid_supplier(vendor, field_label)

    data = {
        "doctype": doctype,
        "job_file": job_file.name,
        "lead": lead.name,
        "status": "Draft"
    }

    if valid_vendor:
        data["assigned_vendor"] = valid_vendor

    doc = frappe.get_doc(data)
    
    # Set flags to allow setting read-only fields
    doc.flags.ignore_permissions = True
    doc.flags.ignore_validate = False
    
    doc.insert()
    
    # Ensure assigned_vendor is saved even if field is read-only
    if valid_vendor and doc.assigned_vendor != valid_vendor:
        frappe.db.set_value(doctype, doc.name, "assigned_vendor", valid_vendor, update_modified=False)
    
    frappe.db.commit()

    return doc


def create_customer_from_lead(lead):
    """
    Create Customer from Lead
    
    Args:
        lead: Lead document
    
    Returns:
        Customer document
    """
    # Check if customer already exists
    customer_name = lead.company_name or f"{lead.first_name} {lead.last_name}"
    
    existing_customer = frappe.db.get_value(
        "Customer",
        {"customer_name": customer_name},
        "name"
    )
    
    if existing_customer:
        return frappe.get_doc("Customer", existing_customer)
    
    # Create new customer
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_type": "Company" if lead.company_name else "Individual",
        "customer_group": "Commercial",
        "territory": "India",
        "gst_category": "Unregistered",
        # Contact details
        "mobile_no": lead.mobile_no,
        "email_id": lead.email_id,
    })
    
    customer.insert(ignore_permissions=True)
    
    # Create Address if available
    if lead.get("custom_address_line_1"):
        create_customer_address(customer.name, lead)
    
    return customer


def create_customer_address(customer_name, lead):
    """Create Address for Customer"""
    try:
        address = frappe.get_doc({
            "doctype": "Address",
            "address_title": customer_name,
            "address_line1": lead.get("custom_address_line_1") or "Not Provided",
            "city": lead.get("city") or "Not Provided",
            "state": lead.get("state") or "Delhi",
            "country": "India",
            "address_type": "Billing",
            "links": [{
                "link_doctype": "Customer",
                "link_name": customer_name
            }]
        })
        address.insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Address creation failed: {str(e)}")


def create_technical_survey_draft(job_file, lead, customer):
    """
    Create Technical Survey in DRAFT status for Job File with vendor assignment from Lead
    NOTE: Status = Draft means vendor can SEE but CANNOT start work yet
    
    Args:
        job_file: Job File document
        lead: Lead document  
        customer: Customer document
        
    Returns:
        Technical Survey document
    """
    # Map phase_type from Lead format to Technical Survey format
    phase_type_mapping = {
        "Single": "Single Phase",
        "Three": "Three Phase"
    }
    
    lead_phase_type = lead.get("custom_phase_type")
    survey_phase_type = phase_type_mapping.get(lead_phase_type, lead_phase_type)
    
    # Get territory from Lead (check all possible fields)
    territory = lead.get("custom_assignment_territory") or lead.get("custom_territory_display") or lead.get("territory")
    
    # Get vendor from Lead - already validated as Supplier
    assigned_vendor = lead.get("vendor_assign")
    
    # Validate it's a Supplier (safety check)
    if assigned_vendor and not frappe.db.exists("Supplier", assigned_vendor):
        frappe.logger().warning(
            f"vendor_assign '{assigned_vendor}' on Lead {lead.name} is not a valid Supplier. "
            "Creating Technical Survey without vendor assignment."
        )
        assigned_vendor = None
    
    
    # CRITICAL: Create in DRAFT status, NOT Scheduled
    tech_survey_data = {
        "doctype": "Technical Survey",
        "job_file": job_file.name,
        "lead": lead.name,
        "customer": customer.name,
        "survey_status": "Pending",
        "status": "Draft",  # CRITICAL: Draft status prevents execution activation
        "phase_type": survey_phase_type,
        "territory": territory,
        "custom_proposed_system": lead.get("custom_proposed_system"),
    }
    
    # Only set assigned_vendor if we have a valid vendor
    if assigned_vendor:
        tech_survey_data["assigned_vendor"] = assigned_vendor
    
    tech_survey = frappe.get_doc(tech_survey_data)
    tech_survey.insert(ignore_permissions=True)
    
    # Log vendor assignment
    if assigned_vendor:
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Technical Survey",
            "reference_name": tech_survey.name,
            "content": f"Vendor {assigned_vendor} assigned from Lead. Status: Draft"
        }).insert(ignore_permissions=True)
    
    return tech_survey


def create_structure_mounting_draft(job_file, lead, customer):
    """
    Create Structure Mounting in DRAFT status
    NOTE: Status = Draft means vendor can SEE but CANNOT start work yet
    
    Args:
        job_file: Job File document
        lead: Lead document
        customer: Customer document
        
    Returns:
        Structure Mounting document
    """
    # Get territory and vendor from Lead
    territory = lead.get("custom_assignment_territory") or lead.get("custom_territory_display") or lead.get("territory")
    assigned_vendor = lead.get("vendor_assign")
    
    # Validate Supplier
    if assigned_vendor and not frappe.db.exists("Supplier", assigned_vendor):
        frappe.logger().warning(f"Invalid vendor on Lead {lead.name}. Creating without vendor.")
        assigned_vendor = None
    
    
    structure_mounting_data = {
        "doctype": "Structure Mounting",
        "job_file": job_file.name,
        "lead": lead.name,
        "status": "Draft",  # CRITICAL: Draft status prevents execution activation
    }
    
    if assigned_vendor:
        structure_mounting_data["assigned_vendor"] = assigned_vendor
    
    structure_mounting = frappe.get_doc(structure_mounting_data)
    structure_mounting.insert(ignore_permissions=True)
    
    return structure_mounting


def create_project_installation_draft(job_file, lead, customer):
    """
    Create Project Installation (Panel Installation) in DRAFT status
    NOTE: Status = Draft means vendor can SEE but CANNOT start work yet
    
    Args:
        job_file: Job File document
        lead: Lead document
        customer: Customer document
        
    Returns:
        Project Installation document
    """
    # Get territory and vendor from Lead
    territory = lead.get("custom_assignment_territory") or lead.get("custom_territory_display") or lead.get("territory")
    assigned_vendor = lead.get("vendor_assign")
    
    # Validate Supplier
    if assigned_vendor and not frappe.db.exists("Supplier", assigned_vendor):
        frappe.logger().warning(f"Invalid vendor on Lead {lead.name}. Creating without vendor.")
        assigned_vendor = None
    
    
    project_installation_data = {
        "doctype": "Project Installation",
        "job_file": job_file.name,
        "lead": lead.name,
        "status": "Draft",  # CRITICAL: Draft status prevents execution activation
    }
    
    if assigned_vendor:
        project_installation_data["assigned_vendor"] = assigned_vendor
    
    project_installation = frappe.get_doc(project_installation_data)
    project_installation.insert(ignore_permissions=True)
    
    return project_installation


def create_meter_installation_draft(job_file, lead, customer):
    """
    Create Meter Installation in DRAFT status
    NOTE: Status = Draft means vendor can SEE but CANNOT start work yet
    
    Args:
        job_file: Job File document
        lead: Lead document
        customer: Customer document
        
    Returns:
        Meter Installation document
    """
    # Get territory and vendor from Lead - use meter_execution_vendor
    territory = lead.get("custom_assignment_territory") or lead.get("custom_territory_display") or lead.get("territory")
    assigned_vendor = lead.get("meter_execution_vendor")
    
    # Validate Supplier
    if assigned_vendor and not frappe.db.exists("Supplier", assigned_vendor):
        frappe.logger().warning(f"Invalid meter vendor on Lead {lead.name}. Creating without vendor.")
        assigned_vendor = None
    
    
    meter_installation_data = {
        "doctype": "Meter Installation",
        "job_file": job_file.name,
        "lead": lead.name,
        "status": "Draft",
    }
    
    if assigned_vendor:
        meter_installation_data["assigned_vendor"] = assigned_vendor
    
    meter_installation = frappe.get_doc(meter_installation_data)
    meter_installation.insert(ignore_permissions=True)
    
    return meter_installation


def create_meter_commissioning_draft(job_file, lead, customer):
    """
    Create Meter Commissioning in DRAFT status
    NOTE: Status = Draft means vendor can SEE but CANNOT start work yet
    
    Args:
        job_file: Job File document
        lead: Lead document
        customer: Customer document
        
    Returns:
        Meter Commissioning document
    """
    # Get territory and vendor from Lead - use meter_execution_vendor
    territory = lead.get("custom_assignment_territory") or lead.get("custom_territory_display") or lead.get("territory")
    assigned_vendor = lead.get("meter_execution_vendor")
    
    # Validate Supplier
    if assigned_vendor and not frappe.db.exists("Supplier", assigned_vendor):
        frappe.logger().warning(f"Invalid meter vendor on Lead {lead.name}. Creating without vendor.")
        assigned_vendor = None
    
    
    meter_commissioning_data = {
        "doctype": "Meter Commissioning",
        "job_file": job_file.name,
        "lead": lead.name,
        "status": "Draft",
    }
    
    if assigned_vendor:
        meter_commissioning_data["assigned_vendor"] = assigned_vendor
    
    meter_commissioning = frappe.get_doc(meter_commissioning_data)
    meter_commissioning.insert(ignore_permissions=True)
    
    return meter_commissioning


def create_verification_handover_draft(job_file, lead, customer):
    """
    Create Verification Handover in DRAFT status
    NOTE: Status = Draft means vendor can SEE but CANNOT start work yet
    
    Args:
        job_file: Job File document
        lead: Lead document
        customer: Customer document
        
    Returns:
        Verification Handover document
    """
    # Get territory and vendor from Lead - use meter_execution_vendor
    territory = lead.get("custom_assignment_territory") or lead.get("custom_territory_display") or lead.get("territory")
    assigned_vendor = lead.get("meter_execution_vendor")
    
    # Validate Supplier
    if assigned_vendor and not frappe.db.exists("Supplier", assigned_vendor):
        frappe.logger().warning(f"Invalid meter vendor on Lead {lead.name}. Creating without vendor.")
        assigned_vendor = None
    
    
    verification_handover_data = {
        "doctype": "Verification Handover",
        "job_file": job_file.name,
        "lead": lead.name,
        "status": "Draft",
    }
    
    if assigned_vendor:
        verification_handover_data["assigned_vendor"] = assigned_vendor
    
    verification_handover = frappe.get_doc(verification_handover_data)
    verification_handover.insert(ignore_permissions=True)
    
    return verification_handover


def create_technical_survey(job_file, lead, customer):
    """
    Legacy function - redirects to create_technical_survey_draft
    Kept for backward compatibility
    """
    return create_technical_survey_draft(job_file, lead, customer)






def validate_and_get_vendor(vendor_identifier):
    """
    Validate that vendor_identifier is a valid Supplier.
    Returns Supplier name if valid, None otherwise.
    
    Args:
        vendor_identifier: Supplier name/ID
        
    Returns:
        Supplier name if valid and exists, None otherwise
    """
    if not vendor_identifier:
        return None
    
    # Reject email addresses immediately
    if '@' in str(vendor_identifier):
        frappe.logger().warning(
            f"Vendor identifier '{vendor_identifier}' appears to be an email. "
            "Vendor fields must contain Supplier IDs only."
        )
        return None
    
    # Check if it's a valid Supplier
    if frappe.db.exists("Supplier", vendor_identifier):
        return vendor_identifier
    
    # Not found
    frappe.logger().warning(
        f"Vendor identifier '{vendor_identifier}' not found in Supplier list"
    )
    return None



# def create_opportunity_from_lead(lead):
#     """
#     Auto-create Opportunity when Lead status becomes 'Contacted'
#     Implements duplicate protection and field mapping
    
#     Args:
#         lead: Lead document
#     """
#     # Duplicate protection - check if Opportunity already exists for this Lead
#     existing_opportunity = frappe.db.get_value(
#         "Opportunity",
#         {"opportunity_from": "Lead", "party_name": lead.name},
#         "name"
#     )
    
#     if existing_opportunity:
#         frappe.msgprint(
#             _("Opportunity {0} already exists for this Lead").format(
#                 frappe.get_desk_link("Opportunity", existing_opportunity)
#             ),
#             indicator="blue",
#             alert=True
#         )
#         return
    
#     try:
#         # Create Opportunity with field mapping
#         opportunity = frappe.get_doc({
#             "doctype": "Opportunity",
#             "opportunity_from": "Lead",
#             "party_name": lead.name,
#             "opportunity_type": "Sales",
#             "status": "Open",
#             # Field mapping from Lead
#             "customer_name": lead.lead_name or f"{lead.first_name} {lead.last_name or ''}".strip(),
#             "contact_email": lead.email_id,
#             "contact_mobile": lead.mobile_no or lead.phone,
#             "territory": lead.territory or lead.get("custom_territory_display") or "All Territories",
#             "company": frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company"),
#             # Source tracking
#             "source": lead.source,
#         })
        
#         # Add custom fields if they exist
#         if lead.get("custom_address_line_1"):
#             opportunity.customer_address = lead.custom_address_line_1
        
#         if lead.get("custom_proposed_system"):
#             # Get item details including rate
#             item_details = frappe.db.get_value(
#                 "Item", 
#                 lead.custom_proposed_system, 
#                 ["standard_rate", "stock_uom"], 
#                 as_dict=True
#             )
            
#             # Add proposed system as an Opportunity item
#             opportunity.append("items", {
#                 "item_code": lead.custom_proposed_system,
#                 "qty": 1,
#                 "uom": item_details.get("stock_uom") if item_details else "Nos",
#                 "rate": item_details.get("standard_rate") if item_details else 0
#             })
        
#         # Set the same lead owner as opportunity owner
#         if lead.lead_owner:
#             opportunity.opportunity_owner = lead.lead_owner
        
#         opportunity.insert(ignore_permissions=True)
#         frappe.db.commit()
#         lead.status = "Contacted"
#         lead.save(ignore_permissions=True)
#         frappe.msgprint(
#             _("Opportunity {0} created successfully from Lead").format(
#                 frappe.get_desk_link("Opportunity", opportunity.name)
#             ),
#             indicator="green",
#             alert=True
#         )
        
#         # Log audit entry
#         frappe.get_doc({
#             "doctype": "Comment",
#             "comment_type": "Info",
#             "reference_doctype": "Lead",
#             "reference_name": lead.name,
#             "content": _("Auto-created Opportunity {0} when Lead status changed to 'Contacted'").format(opportunity.name)
#         }).insert(ignore_permissions=True)
        
#     except Exception as e:
#         frappe.log_error(
#             title=_("Opportunity Creation Failed for Lead {0}").format(lead.name),
#             message=frappe.get_traceback()
#         )
#         frappe.msgprint(
#             _("Failed to create Opportunity: {0}").format(str(e)),
#             indicator="red",
#             alert=True
#         )


def auto_create_customer_on_qualified(lead):
    """
    Auto-create Customer when Lead status becomes 'Qualified'
    Also links any existing Opportunity to the Customer
    
    Args:
        lead: Lead document
    """
    # Duplicate protection - check if Customer already exists
    customer_name_candidate = lead.company_name or f"{lead.first_name} {lead.last_name or ''}".strip()
    
    existing_customer = frappe.db.get_value(
        "Customer",
        {"customer_name": customer_name_candidate},
        "name"
    )
    
    if existing_customer:
        frappe.msgprint(
            _("Customer {0} already exists for this Lead").format(
                frappe.get_desk_link("Customer", existing_customer)
            ),
            indicator="blue",
            alert=True
        )
        # Link existing Opportunity to Customer if exists
        link_opportunity_to_customer(lead, existing_customer)
        return
    
    try:
        # Create Customer with field mapping
        customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": customer_name_candidate,
            "customer_type": "Company" if lead.company_name else "Individual",
            "customer_group": "Commercial",  # Default customer group
            "territory": lead.territory or lead.get("custom_territory_display") or "All Territories",
            # Contact details
            "mobile_no": lead.mobile_no,
            "email_id": lead.email_id,
            # GST details if available
            "gst_category": "Unregistered",  # Default
        })
        
        # Add GSTIN if available
        if lead.get("gstin"):
            customer.gstin = lead.gstin
            customer.gst_category = "Registered Regular"
        
        customer.insert(ignore_permissions=True)
        
        # Create Address if available
        if lead.get("custom_address_line_1") or lead.get("city"):
            create_customer_address(customer.name, lead)
        
        frappe.db.commit()
        
        frappe.msgprint(
            _("Customer {0} created successfully from Lead").format(
                frappe.get_desk_link("Customer", customer.name)
            ),
            indicator="green",
            alert=True
        )
        
        # Log audit entry
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Lead",
            "reference_name": lead.name,
            "content": _("Auto-created Customer {0} when Lead status changed to 'Qualified'").format(customer.name)
        }).insert(ignore_permissions=True)
        
        # Link any existing Opportunity to this Customer
        link_opportunity_to_customer(lead, customer.name)
        
    except Exception as e:
        frappe.log_error(
            title=_("Customer Creation Failed for Lead {0}").format(lead.name),
            message=frappe.get_traceback()
        )
        frappe.msgprint(
            _("Failed to create Customer: {0}").format(str(e)),
            indicator="red",
            alert=True
        )


def link_opportunity_to_customer(lead, customer_name):
    """
    Link existing Opportunity to Customer
    
    Args:
        lead: Lead document
        customer_name: Customer name to link to
    """
    # Find Opportunity linked to this Lead
    opportunity = frappe.db.get_value(
        "Opportunity",
        {"opportunity_from": "Lead", "party_name": lead.name},
        "name"
    )
    
    if opportunity:
        try:
            # Update Opportunity to link to Customer
            frappe.db.set_value("Opportunity", opportunity, {
                "opportunity_from": "Customer",
                "party_name": customer_name
            }, update_modified=True)
            
            frappe.db.commit()
            
            frappe.msgprint(
                _("Opportunity {0} linked to Customer {1}").format(
                    frappe.get_desk_link("Opportunity", opportunity),
                    frappe.get_desk_link("Customer", customer_name)
                ),
                indicator="green",
                alert=True
            )
            
            # Log audit entry
            frappe.get_doc({
                "doctype": "Comment",
                "comment_type": "Info",
                "reference_doctype": "Opportunity",
                "reference_name": opportunity,
                "content": _("Linked to Customer {0} when Lead was qualified").format(customer_name)
            }).insert(ignore_permissions=True)
            
        except Exception as e:
            frappe.log_error(
                title=_("Failed to link Opportunity {0} to Customer").format(opportunity),
                message=frappe.get_traceback()
            )

