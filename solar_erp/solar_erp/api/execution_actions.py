# Copyright (c) 2025, KaitenSoftware
# Unified Execution Actions API
# Provides consistent action handlers across all execution doctypes

import frappe
from frappe import _
from frappe.utils import now_datetime

from solar_erp.solar_erp.api.execution_workflow import (
    is_admin_user,
    get_next_stage,
    get_vendor_from_previous_stages,
    can_start_stage
)


# Allowed status transitions
STATUS_TRANSITIONS = {
    # Status: {action: next_status}
    "Draft": {
        "start": "In Progress"
    },
    "Scheduled": {
        "start": "In Progress",
        "hold": "On Hold"
    },
    "In Progress": {
        "submit": "In Review",  # Default for Technical Survey
        "hold": "On Hold"
    },
    "On Hold": {
        "reopen": "Reopened"
    },
    "Reopened": {
        "start": "In Progress",
        "hold": "On Hold"
    },
    "In Review": {
        "approve": "Approved",
        "rework": "Rework"
    },
    "Submitted": {
        "approve": "Approved",
        "rework": "Rejected"
    },
    "Ready for Review": {
        "approve": "Approved",
        "rework": "Rework"
    },
    "Rework": {
        "start": "In Progress"
    },
    "Approved": {
        "close": "Closed"
    },
    "Closed": {
        "reopen": "Reopened"
    }
}

# Doctype-specific status for submit action
# Each doctype uses different status names
DOCTYPE_SUBMIT_STATUS = {
    "Technical Survey": "In Review",
    "Structure Mounting": "Submitted",
    "Panel Installation": "Ready for Review",
    "Meter Installation": "Ready for Review",
    "Meter Commissioning": "Ready for Review",
    "Verification Handover": "Ready for Review"
}

# Actions allowed by role
VENDOR_EXECUTIVE_ACTIONS = ["start", "submit", "hold"]
PROJECT_MANAGER_ACTIONS = ["approve", "rework", "close", "reopen"]


def check_role_permission(action):
    """
    Check if current user has permission for the action
    Returns True if allowed, raises exception if not
    """
    if is_admin_user():
        return True
    
    user_roles = frappe.get_roles()
    
    if action in VENDOR_EXECUTIVE_ACTIONS:
        if "Vendor Executive" in user_roles:
            return True
        frappe.throw(
            _("Only Vendor Executive can perform '{0}' action").format(action),
            title=_("Permission Denied")
        )
    
    if action in PROJECT_MANAGER_ACTIONS:
        if "Project Manager" in user_roles:
            return True
        frappe.throw(
            _("Only Project Manager can perform '{0}' action").format(action),
            title=_("Permission Denied")
        )
    
    frappe.throw(_("Unknown action: {0}").format(action))


def validate_transition(current_status, action):
    """
    Validate status transition is allowed
    """
    allowed_actions = STATUS_TRANSITIONS.get(current_status, {})
    
    if action not in allowed_actions:
        frappe.throw(
            _("Action '{0}' is not allowed when status is '{1}'").format(action, current_status),
            title=_("Invalid Transition")
        )
    
    return allowed_actions[action]


def log_action(doc, action, comment, user=None):
    """
    Log action to Comments and Version history
    """
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": doc.doctype,
        "reference_name": doc.name,
        "content": _("{0} performed '{1}' action. Comment: {2}").format(
            user or frappe.session.user,
            action.title(),
            comment or "N/A"
        )
    }).insert(ignore_permissions=True)


def create_next_stage(doc):
    """
    Auto-create the next execution stage document
    """
    doctype_map = {
        "Technical Survey": ("Structure Mounting", "linked_structure_mounting"),
        "Structure Mounting": ("Panel Installation", "linked_panel_installation"),
        "Panel Installation": ("Meter Installation", "linked_meter_installation"),
        "Meter Installation": ("Meter Commissioning", "linked_meter_commissioning"),
        "Meter Commissioning": ("Verification Handover", "linked_verification_handover")
    }
    
    if doc.doctype not in doctype_map:
        return None
    
    next_doctype, link_field = doctype_map[doc.doctype]
    
    # Check if already exists
    existing = frappe.db.get_value(next_doctype, {"job_file": doc.job_file}, "name")
    if existing:
        # Link it if not already linked
        if hasattr(doc, link_field) and not doc.get(link_field):
            doc.db_set(link_field, existing)
        return existing
    
    # Get vendor from current doc or previous stages
    vendor = doc.get("assigned_vendor") or get_vendor_from_previous_stages(doc.job_file)
    
    # Validate vendor is actually a Supplier before assigning
    if vendor and not frappe.db.exists("Supplier", vendor):
        frappe.logger().warning(
            f"Vendor '{vendor}' is not a valid Supplier. Skipping vendor assignment for {next_doctype}"
        )
        vendor = None
    
    # Build the new doc
    parent_link_map = {
        "Structure Mounting": ("technical_survey", doc.name if doc.doctype == "Technical Survey" else None),
        "Panel Installation": ("structure_mounting", doc.name if doc.doctype == "Structure Mounting" else None),
        "Meter Installation": ("panel_installation", doc.name if doc.doctype == "Panel Installation" else None),
        "Meter Commissioning": ("meter_installation", doc.name if doc.doctype == "Meter Installation" else None),
        "Verification Handover": ("meter_commissioning", doc.name if doc.doctype == "Meter Commissioning" else None)
    }
    
    new_doc_data = {
        "doctype": next_doctype,
        "job_file": doc.job_file,
        "status": "Draft",
        "workflow_state": "Draft"  # Keep workflow_state in sync with status
    }
    
    # Only add vendor if valid
    if vendor:
        new_doc_data["assigned_vendor"] = vendor
    
    # Add parent link field
    parent_field, parent_value = parent_link_map.get(next_doctype, (None, None))
    if parent_field and parent_value:
        new_doc_data[parent_field] = parent_value
    
    new_doc = frappe.get_doc(new_doc_data)
    new_doc.flags.ignore_permissions = True
    new_doc.insert()
    
    # Update link field on current doc
    if hasattr(doc, link_field):
        doc.db_set(link_field, new_doc.name)
    
    return new_doc.name


def update_job_file_status(job_file, completed_stage):
    """
    Update Job File current_step and last_step_completed
    """
    stage_order = [
        "Technical Survey",
        "Structure Mounting",
        "Panel Installation",
        "Meter Installation",
        "Meter Commissioning",
        "Verification & Handover"
    ]
    
    # Map doctype stage to job file stage names
    stage_map = {
        "Technical Survey": "Technical Survey",
        "Structure Mounting": "Structure Mounting",
        "Panel Installation": "Panel Installation",
        "Meter Installation": "Meter Installation",
        "Meter Commissioning": "Meter Commissioning",
        "Verification Handover": "Verification & Handover"
    }
    
    jf_stage = stage_map.get(completed_stage)
    if not jf_stage:
        return
    
    jf = frappe.get_doc("Job File", job_file)
    jf.last_step_completed = jf_stage
    
    # Set next step as current
    if jf_stage in stage_order:
        idx = stage_order.index(jf_stage)
        if idx < len(stage_order) - 1:
            jf.current_step = stage_order[idx + 1]
        else:
            jf.current_step = "Completed"
            jf.overall_status = "Completed"
    
    jf.save(ignore_permissions=True)


def set_status_and_workflow(doc, new_status):
    """
    Set both status and workflow_state to keep them synchronized
    This prevents list view (workflow_state) and form view (status) mismatches
    """
    doc.status = new_status
    doc.workflow_state = new_status


# =============================================================================
# WHITELISTED ACTION APIS
# =============================================================================

@frappe.whitelist()
def start_work(doctype, docname):
    """
    Start work on an execution stage
    Vendor Executive action
    """
    check_role_permission("start")
    
    doc = frappe.get_doc(doctype, docname)
    next_status = validate_transition(doc.status, "start")
    
    # Special handling for Technical Survey: Auto-set survey_date (one-time only)
    if doctype == "Technical Survey":
        if not doc.get("survey_date"):
            doc.survey_date = frappe.utils.today()
    
    set_status_and_workflow(doc, next_status)
    doc.save(ignore_permissions=True)
    
    log_action(doc, "start", "Work started")
    
    return {
        "status": "success",
        "message": _("Work started on {0}").format(docname),
        "new_status": next_status
    }


@frappe.whitelist()
def hold_work(doctype, docname, reason):
    """
    Put work on hold
    Vendor Executive action - reason mandatory
    """
    if not reason:
        frappe.throw(_("Reason is mandatory for Hold action"))
    
    check_role_permission("hold")
    
    doc = frappe.get_doc(doctype, docname)
    next_status = validate_transition(doc.status, "hold")
    
    set_status_and_workflow(doc, next_status)
    doc.workflow_reason = reason
    doc.save(ignore_permissions=True)
    
    log_action(doc, "hold", reason)
    
    return {
        "status": "success",
        "message": _("{0} put on hold").format(docname),
        "new_status": next_status
    }


@frappe.whitelist()
def submit_for_review(doctype, docname):
    """
    Submit work for review
    Vendor Executive action
    Uses doctype-specific status (In Review for Technical Survey, Ready for Review for others)
    """
    check_role_permission("submit")
    
    doc = frappe.get_doc(doctype, docname)
    
    # Get doctype-specific submit status
    next_status = DOCTYPE_SUBMIT_STATUS.get(doctype, "In Review")  # Default to "In Review"
    
    # Validate current status allows submit
    if doc.status != "In Progress":
        frappe.throw(
            _("Can only submit from 'In Progress' status. Current status: {0}").format(doc.status),
            title=_("Invalid Status")
        )
    
    set_status_and_workflow(doc, next_status)
    doc.save(ignore_permissions=True)
    
    log_action(doc, "submit", "Submitted for review")
    
    return {
        "status": "success",
        "message": _("{0} submitted for review").format(docname),
        "new_status": next_status
    }


@frappe.whitelist()
def approve(doctype, docname, comment):
    """
    Approve an execution stage
    Project Manager action - comment mandatory
    Creates next stage automatically
    For Technical Survey: Also creates Quotation
    """
    if not comment:
        frappe.throw(_("Comment is mandatory for Approve action"))
    
    check_role_permission("approve")
    
    doc = frappe.get_doc(doctype, docname)
    next_status = validate_transition(doc.status, "approve")
    
    set_status_and_workflow(doc, next_status)
    doc.workflow_reason = comment
    doc.reviewer = frappe.session.user
    doc.review_decision = "Approved"
    doc.review_comments = comment
    doc.save(ignore_permissions=True)
    
    log_action(doc, "approve", comment)
    
    result = {
        "status": "success",
        "message": _("{0} approved").format(docname),
        "new_status": next_status
    }
    
    # Special handling for Technical Survey - create Quotation
    if doctype == "Technical Survey":
        quotation = create_quotation_from_technical_survey(doc)
        if quotation:
            result["quotation_created"] = quotation
            result["message"] = _("{0} approved. Quotation {1} created.").format(docname, quotation)
    
    # Auto-create next stage
    next_doc = create_next_stage(doc)
    
    # Update Job File
    update_job_file_status(doc.job_file, doc.doctype)
    
    if next_doc:
        result["next_stage_created"] = next_doc
        if "quotation_created" in result:
            result["message"] = _("{0} approved. Quotation {1} and next stage {2} created.").format(
                docname, result["quotation_created"], next_doc
            )
        else:
            result["message"] = _("{0} approved. Next stage {1} created.").format(docname, next_doc)
    
    return result


def create_quotation_from_technical_survey(tech_survey):
    """
    Create a Quotation from an approved Technical Survey
    """
    # Check if quotation already exists for this technical survey
    existing = frappe.db.get_value("Quotation", {"custom_technical_survey": tech_survey.name}, "name")
    if existing:
        frappe.msgprint(
            _("Quotation {0} already exists for this Technical Survey").format(existing),
            indicator="blue",
            alert=True
        )
        return existing
    
    # Get customer from Job File or Lead
    customer = None
    if tech_survey.job_file:
        customer = frappe.db.get_value("Job File", tech_survey.job_file, "customer")
    
    if not customer and tech_survey.lead:
        # Try to get customer created from lead
        lead = frappe.get_doc("Lead", tech_survey.lead)
        customer_name = lead.company_name or f"{lead.first_name} {lead.last_name or ''}"
        customer = frappe.db.get_value("Customer", {"customer_name": customer_name.strip()}, "name")
    
    if not customer:
        frappe.msgprint(
            _("Could not find Customer for Quotation. Please create manually."),
            indicator="orange",
            alert=True
        )
        return None
    
    # Get proposed system item from technical survey
    proposed_system = tech_survey.get("custom_proposed_system") or tech_survey.get("proposed_system")
    
    try:
        # Create Quotation
        quotation = frappe.get_doc({
            "doctype": "Quotation",
            "quotation_to": "Customer",
            "party_name": customer,
            "custom_technical_survey": tech_survey.name,
            "custom_job_file": tech_survey.job_file,
            "transaction_date": frappe.utils.today(),
            "valid_till": frappe.utils.add_days(frappe.utils.today(), 30),
            "custom_quotation_status": "Draft"
        })
        
        # Add proposed system as line item if available
        if proposed_system:
            # Check if item exists
            if frappe.db.exists("Item", proposed_system):
                item_doc = frappe.get_doc("Item", proposed_system)
                quotation.append("items", {
                    "item_code": proposed_system,
                    "item_name": item_doc.item_name,
                    "qty": 1,
                    "uom": item_doc.stock_uom or "Nos",
                    "rate": item_doc.standard_rate or 0
                })
        
        quotation.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.msgprint(
            _("Quotation {0} created for Customer {1}").format(
                frappe.get_desk_link("Quotation", quotation.name),
                customer
            ),
            indicator="green",
            alert=True
        )
        
        return quotation.name
        
    except Exception as e:
        frappe.log_error(
            title=_("Quotation Creation Failed for TS {0}").format(tech_survey.name),
            message=frappe.get_traceback()
        )
        frappe.msgprint(
            _("Failed to create Quotation: {0}. Please create manually.").format(str(e)),
            indicator="red",
            alert=True
        )
        return None


@frappe.whitelist()
def request_rework(doctype, docname, comment):
    """
    Request rework on a stage
    Project Manager action - comment mandatory
    """
    if not comment:
        frappe.throw(_("Comment is mandatory for Rework action"))
    
    check_role_permission("rework")
    
    doc = frappe.get_doc(doctype, docname)
    next_status = validate_transition(doc.status, "rework")
    
    set_status_and_workflow(doc, next_status)
    doc.workflow_reason = comment
    doc.reviewer = frappe.session.user
    doc.review_decision = "Rework"
    doc.review_comments = comment
    doc.save(ignore_permissions=True)
    
    log_action(doc, "rework", comment)
    
    return {
        "status": "success",
        "message": _("Rework requested on {0}").format(docname),
        "new_status": next_status
    }


@frappe.whitelist()
def close_stage(doctype, docname, comment):
    """
    Close an execution stage
    Project Manager action - comment mandatory
    """
    if not comment:
        frappe.throw(_("Comment is mandatory for Close action"))
    
    check_role_permission("close")
    
    doc = frappe.get_doc(doctype, docname)
    next_status = validate_transition(doc.status, "close")
    
    set_status_and_workflow(doc, next_status)
    doc.workflow_reason = comment
    doc.save(ignore_permissions=True)
    
    log_action(doc, "close", comment)
    
    return {
        "status": "success",
        "message": _("{0} closed").format(docname),
        "new_status": next_status
    }


@frappe.whitelist()
def reopen_stage(doctype, docname, comment):
    """
    Reopen a closed/on-hold stage
    Project Manager action - comment mandatory
    """
    if not comment:
        frappe.throw(_("Comment is mandatory for Reopen action"))
    
    check_role_permission("reopen")
    
    doc = frappe.get_doc(doctype, docname)
    next_status = validate_transition(doc.status, "reopen")
    
    set_status_and_workflow(doc, next_status)
    doc.workflow_reason = comment
    doc.save(ignore_permissions=True)
    
    log_action(doc, "reopen", comment)
    
    return {
        "status": "success",
        "message": _("{0} reopened").format(docname),
        "new_status": next_status
    }


@frappe.whitelist()
def get_available_actions(doctype, docname):
    """
    Get list of available actions for current user and status
    """
    doc = frappe.get_doc(doctype, docname)
    current_status = doc.status
    
    allowed_transitions = STATUS_TRANSITIONS.get(current_status, {})
    user_roles = frappe.get_roles()
    is_admin = is_admin_user()
    
    available_actions = []
    
    for action in allowed_transitions.keys():
        if is_admin:
            available_actions.append(action)
        elif action in VENDOR_EXECUTIVE_ACTIONS and "Vendor Executive" in user_roles:
            available_actions.append(action)
        elif action in PROJECT_MANAGER_ACTIONS and "Project Manager" in user_roles:
            available_actions.append(action)
    
    return {
        "current_status": current_status,
        "available_actions": available_actions,
        "is_admin": is_admin
    }
