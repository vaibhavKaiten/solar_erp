# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class TechnicalSurvey(Document):
    def validate(self):
        """Validate the document before saving"""
        # Prevent manual creation
        if self.is_new() and not self.job_file:
            if not self.flags.ignore_permissions:
                frappe.throw(
                    _("Technical Survey can only be created automatically when Lead initiates job. "
                      "Please use the 'Initiate Job' action on the Lead."),
                    title=_("Manual Creation Not Allowed")
                )
        
        # Skip validation if called from action method
        if self.flags.get("from_action_method"):
            return
        
        # Validate Survey Start Date cannot be changed once set
        if not self.is_new():
            old_doc = self.get_doc_before_save()
            if old_doc and old_doc.survey_date:
                # Once survey_date is set, it can NEVER be changed
                if str(self.survey_date) != str(old_doc.survey_date):
                    frappe.throw(
                        _("Survey Start Date cannot be modified once set. Original date: {0}").format(
                            frappe.format(old_doc.survey_date, {"fieldtype": "Date"})
                        ),
                        title=_("Field Locked")
                    )
        
        # Lock editing after Submitted - check PREVIOUS status, not current
        if not self.is_new():
            old_doc = self.get_doc_before_save()
            # Only lock if the PREVIOUS status was in locked statuses
            if old_doc and old_doc.status in ["In Review", "Approved", "Closed"]:
                # Only allow Manager to make changes
                if not self._has_manager_role():
                    # Check if any important fields changed
                    if self._has_data_changed(old_doc):
                        frappe.throw(
                            _("Cannot edit after submission. Contact a manager for changes."),
                            title=_("Editing Locked")
                        )
    
    def _has_manager_role(self):
        """Check if current user has Manager role"""
        return (
            frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Technical Survey Manager"}) or
            "System Manager" in frappe.get_roles() or
            "Administrator" in frappe.get_roles()
        )
    
    def _has_data_changed(self, old_doc):
        """Check if important data fields have changed"""
        ignore_fields = ["status", "workflow_reason", "reviewer", "review_decision", "review_comments", "modified", "modified_by"]
        for field in self.meta.fields:
            if field.fieldname not in ignore_fields:
                if self.get(field.fieldname) != old_doc.get(field.fieldname):
                    return True
        return False

    def on_update(self):
        """
        Trigger triggers on status change
        """
        # Trigger automation on approval (status change to Approved)
        if self.status == "Approved":
            # Check if status just changed to Approved
            old_doc = self.get_doc_before_save()
            if old_doc and old_doc.status != "Approved":
                self.auto_create_subsidy_loan_applications()
    
    def auto_create_subsidy_loan_applications(self):
        """
        Auto-create Subsidy Application and Bank Loan Application
        Based on checkboxes: subsidy_required, bank_loan_required
        """
        # Fetch Lead details
        if not self.lead:
            return
            
        lead_doc = frappe.get_doc("Lead", self.lead)
        
        # CASE 1: Subsidy Application
        if self.subsidy_required:
            # Check for existing
            exists = frappe.db.exists("Subsidy Application", {
                "lead": self.lead,
                "technical_survey": self.name
            })
            
            if not exists:
                try:
                    subsidy_doc = frappe.get_doc({
                        "doctype": "Subsidy Application",
                        "status": "Draft",
                        "scheme": "PM-Surya Ghar", # Default
                        "lead": self.lead,
                        "customer": self.customer,
                        "technical_survey": self.name,
                        "project": self.project,
                        "territory": self.territory,
                        "first_name": lead_doc.first_name,
                        "last_name": lead_doc.last_name,
                        "whatsapp_number": lead_doc.mobile_no,
                        "contact_number": lead_doc.mobile_no,
                        "email_id": lead_doc.email_id,
                        "address_line_1": lead_doc.custom_address_line_1,
                        "city": lead_doc.city,
                        "state": lead_doc.state,
                    })
                    
                    # Optional fields
                    if self.proposed_system_size_kw:
                        subsidy_doc.system_capacity = self.proposed_system_size_kw
                    
                    subsidy_doc.insert(ignore_permissions=True)
                    
                    # Log
                    frappe.get_doc({
                       "doctype": "Comment",
                       "comment_type": "Info",
                       "reference_doctype": "Technical Survey",
                       "reference_name": self.name,
                       "content": _("Auto-created Subsidy Application: {0}").format(subsidy_doc.name)
                    }).insert(ignore_permissions=True)

                except Exception as e:
                    frappe.log_error(f"Failed to create Subsidy Application: {str(e)}", "Auto Creation Error")
        
        # CASE 2: Bank Loan Application
        if self.bank_loan_required:
             # Check for existing
            exists = frappe.db.exists("Bank Loan Application", {
                "lead": self.lead,
                "technical_survey": self.name
            })
            
            if not exists:
                try:
                    loan_doc = frappe.get_doc({
                        "doctype": "Bank Loan Application",
                        "lead": self.lead,
                        "technical_survey": self.name,
                        "project": self.project,
                        "first_name": lead_doc.first_name,
                        "last_name": lead_doc.last_name,
                        "whatsapp_number": lead_doc.mobile_no,
                        "contact_number": lead_doc.mobile_no,
                        "email_id": lead_doc.email_id,
                        "mobile_no": lead_doc.mobile_no,
                        "address_line_1": lead_doc.custom_address_line_1,
                        "city": lead_doc.city,
                        "state": lead_doc.state,
                        "loan_amount": 0, # Mandatory
                    })
                    
                    if self.proposed_system_size_kw:
                        loan_doc.system_capacity_kw = self.proposed_system_size_kw
                        
                    loan_doc.insert(ignore_permissions=True)
                    
                    # Log
                    frappe.get_doc({
                       "doctype": "Comment",
                       "comment_type": "Info",
                       "reference_doctype": "Technical Survey",
                       "reference_name": self.name,
                       "content": _("Auto-created Bank Loan Application: {0}").format(loan_doc.name)
                    }).insert(ignore_permissions=True)
                    
                except Exception as e:
                    frappe.log_error(f"Failed to create Bank Loan Application: {str(e)}", "Auto Creation Error")


# =============================================================================
# EXECUTIVE ACTIONS
# =============================================================================

@frappe.whitelist()
def start_work(docname):
    """
    Start work - transitions from Scheduled/Reopened to In Progress
    Executive action
    """
    doc = frappe.get_doc("Technical Survey", docname)
    
    if doc.status not in ["Scheduled", "Reopened"]:
        frappe.throw(_("Can only start work when status is Scheduled or Reopened"))
    
    # Check if user has the right role
    if not _has_executive_or_manager_role():
        frappe.throw(_("You don't have permission to start this work"))
    
    # Auto-set Survey Start Date (one-time only)
    # Only set if it's empty - never overwrite once set
    if not doc.survey_date:
        doc.survey_date = frappe.utils.today()
    
    doc.status = "In Progress"
    doc.flags.ignore_permissions = True
    doc.flags.from_action_method = True
    doc.save()
    frappe.db.commit()
    
    _log_status_change(doc.name, "Started work", "In Progress")
    
    return {"status": "success", "message": _("Work started successfully")}


@frappe.whitelist()
def hold_work(docname, reason):
    """
    Put work on hold - Executive action
    From: Scheduled, In Progress
    To: On Hold
    """
    doc = frappe.get_doc("Technical Survey", docname)
    
    if doc.status not in ["Scheduled", "In Progress"]:
        frappe.throw(_("Can only hold when status is Scheduled or In Progress"))
    
    # Check if user has the right role
    if not _has_executive_role():
        frappe.throw(_("Only Technical Survey Executive can put work on hold"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for putting on hold"))
    
    doc.status = "On Hold"
    doc.workflow_reason = reason
    doc.flags.ignore_permissions = True
    doc.flags.from_action_method = True
    doc.save()
    frappe.db.commit()
    
    _log_status_change(doc.name, reason, "On Hold")
    
    return {"status": "success", "message": _("Work put on hold")}


@frappe.whitelist()
def submit_survey(docname):
    """
    Submit survey for review - locks editing
    Executive action
    From: In Progress
    To: In Review
    """
    doc = frappe.get_doc("Technical Survey", docname)
    
    if doc.status != "In Progress":
        frappe.throw(_("Can only submit when status is In Progress"))
    
    # Check if user has the right role
    if not _has_executive_role():
        frappe.throw(_("Only Technical Survey Executive can submit survey"))
    
    # Validate submission checklist
    if not doc.get("bom_verified"):
        frappe.throw(_("Please verify BOM before submitting for review"), title=_("BOM Verification Required"))
    
    if not doc.get("client_agreement"):
        frappe.throw(_("Please confirm Client Agreement before submitting for review"), title=_("Client Agreement Required"))
    
    doc.status = "In Review"
    doc.flags.ignore_permissions = True
    doc.flags.from_action_method = True
    doc.save()
    frappe.db.commit()
    
    _log_status_change(doc.name, "Submitted for review", "In Review")
    
    return {"status": "success", "message": _("Survey submitted for review")}


# =============================================================================
# MANAGER ACTIONS
# =============================================================================

@frappe.whitelist()
def approve_survey(docname, comment):
    """
    Approve survey - Manager action
    From: In Review
    To: Approved
    """
    doc = frappe.get_doc("Technical Survey", docname)
    
    if doc.status != "In Review":
        frappe.throw(_("Can only approve when status is In Review"))
    
    # Check if user has the right role (Manager only)
    if not _has_manager_role():
        frappe.throw(_("Only Technical Survey Manager can approve"))
    
    if not comment or comment.strip() == "":
        frappe.throw(_("Please provide a comment for approval"))
    
    doc.status = "Approved"
    doc.workflow_reason = comment
    doc.reviewer = frappe.session.user
    doc.review_decision = "Approved"
    doc.review_comments = comment
    doc.flags.ignore_permissions = True
    doc.flags.from_action_method = True
    doc.save()
    frappe.db.commit()
    
    _log_status_change(doc.name, comment, "Approved")
    
    # AUTO-CREATE QUOTATION
    quotation_name = _auto_create_quotation(doc)
    
    return {
        "status": "success", 
        "message": _("Survey approved"),
        "quotation_created": True if quotation_name else False,
        "quotation_name": quotation_name
    }


@frappe.whitelist()
def close_survey(docname, reason):
    """
    Close survey - Manager action
    From: Any active status
    To: Closed
    """
    doc = frappe.get_doc("Technical Survey", docname)
    
    # Can close from any active status except already Closed
    if doc.status == "Closed":
        frappe.throw(_("Survey is already closed"))
    
    # Check if user has the right role (Manager only)
    if not _has_manager_role():
        frappe.throw(_("Only Technical Survey Manager can close"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for closing"))
    
    doc.status = "Closed"
    doc.workflow_reason = reason
    doc.flags.ignore_permissions = True
    doc.flags.from_action_method = True
    doc.save()
    frappe.db.commit()
    
    _log_status_change(doc.name, reason, "Closed")
    
    return {"status": "success", "message": _("Survey closed")}


@frappe.whitelist()
def reopen_survey(docname, reason):
    """
    Reopen survey - Manager action
    From: Closed, On Hold
    To: Reopened
    """
    doc = frappe.get_doc("Technical Survey", docname)
    
    if doc.status not in ["Closed", "On Hold"]:
        frappe.throw(_("Can only reopen when status is Closed or On Hold"))
    
    # Check if user has the right role (Manager only)
    if not _has_manager_role():
        frappe.throw(_("Only Technical Survey Manager can reopen"))
    
    if not reason or reason.strip() == "":
        frappe.throw(_("Please provide a reason for reopening"))
    
    doc.status = "Reopened"
    doc.workflow_reason = reason
    doc.flags.ignore_permissions = True
    doc.flags.from_action_method = True
    doc.save()
    frappe.db.commit()
    
    _log_status_change(doc.name, reason, "Reopened")
    
    return {"status": "success", "message": _("Survey reopened. Vendor can now resume work.")}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _has_executive_role():
    """Check if current user has Executive role"""
    return (
        frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Technical Survey Executive"}) or
        "System Manager" in frappe.get_roles() or
        "Administrator" in frappe.get_roles()
    )


def _has_manager_role():
    """Check if current user has Manager role"""
    return (
        frappe.db.exists("Has Role", {"parent": frappe.session.user, "role": "Technical Survey Manager"}) or
        "System Manager" in frappe.get_roles() or
        "Administrator" in frappe.get_roles()
    )


def _has_executive_or_manager_role():
    """Check if current user has Executive or Manager role"""
    return _has_executive_role() or _has_manager_role()


def _log_status_change(docname, comment, new_status):
    """Log status change as comment for audit"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Technical Survey",
        "reference_name": docname,
        "content": _("Status changed to {0}. {1}").format(new_status, comment)
    }).insert(ignore_permissions=True)


def _auto_create_quotation(survey_doc):
    """
    Auto-create Quotation when Technical Survey is approved
    Populates BOM data from Technical Survey
    """
    # Check if quotation already exists
    existing = frappe.db.exists("Quotation", {"custom_technical_survey": survey_doc.name})
    if existing:
        frappe.log_error(f"Quotation {existing} already exists for Technical Survey {survey_doc.name}")
        return existing
    
    try:
        # Get Job File for lead info
        job_file = frappe.get_doc("Job File", survey_doc.job_file)
        
        # Create Quotation
        quotation = frappe.get_doc({
            "doctype": "Quotation",
            "quotation_to": "Lead",
            "party_name": survey_doc.lead,
            "transaction_date": frappe.utils.today(),
            "custom_quotation_status": "Draft",
            "custom_technical_survey": survey_doc.name,
            "custom_proposed_system": survey_doc.get("proposed_system") or survey_doc.get("custom_proposed_system"),
        })
        
        # Add proposed system as main item
        proposed_system = survey_doc.get("proposed_system") or survey_doc.get("custom_proposed_system")
        if proposed_system:
            item_details = frappe.db.get_value("Item", proposed_system, 
                ["description", "standard_rate"], as_dict=True)
            
            quotation.append("items", {
                "item_code": proposed_system,
                "qty": 1,
                "rate": item_details.standard_rate if item_details else 0,
                "description": item_details.description if item_details else ""
            })
        
        # Auto-populate BOM items from Technical Survey
        # Panel
        if survey_doc.get("selected_panel"):
            panel_qty = survey_doc.get("panel_qty_from_bom") or 1
            panel_rate = frappe.db.get_value("Item", survey_doc.selected_panel, "standard_rate") or 0
            quotation.append("items", {
                "item_code": survey_doc.selected_panel,
                "qty": panel_qty,
                "rate": panel_rate,
                "description": f"Solar Panel - {survey_doc.selected_panel}"
            })
        
        # Inverter
        if survey_doc.get("selected_inverter"):
            inverter_qty = survey_doc.get("inverter_qty_from_bom") or 1
            inverter_rate = frappe.db.get_value("Item", survey_doc.selected_inverter, "standard_rate") or 0
            quotation.append("items", {
                "item_code": survey_doc.selected_inverter,
                "qty": inverter_qty,
                "rate": inverter_rate,
                "description": f"Inverter - {survey_doc.selected_inverter}"
            })
        
        # Battery (if any)
        if survey_doc.get("selected_battery"):
            battery_qty = survey_doc.get("battery_qty_from_bom") or 1
            battery_rate = frappe.db.get_value("Item", survey_doc.selected_battery, "standard_rate") or 0
            quotation.append("items", {
                "item_code": survey_doc.selected_battery,
                "qty": battery_qty,
                "rate": battery_rate,
                "description": f"Battery - {survey_doc.selected_battery}"
            })
        
        # Other BOM items
        if survey_doc.get("bom_other_items"):
            for bom_item in survey_doc.bom_other_items:
                item_rate = frappe.db.get_value("Item", bom_item.item, "standard_rate") or 0
                quotation.append("items", {
                    "item_code": bom_item.item,
                    "qty": bom_item.qty,
                    "rate": item_rate,
                    "description": bom_item.get("notes") or ""
                })
        
        quotation.flags.ignore_mandatory = True
        quotation.insert(ignore_permissions=True)
        
        # Log audit
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": "Quotation",
            "reference_name": quotation.name,
            "content": _("Quotation auto-created from Technical Survey {0}").format(survey_doc.name)
        }).insert(ignore_permissions=True)
        
        frappe.db.commit()
        
        return quotation.name
        
    except Exception as e:
        frappe.log_error(
            title=_("Quotation Auto-Creation Failed"),
            message=f"Failed to create quotation for Technical Survey {survey_doc.name}: {str(e)}"
        )
        return None


def find_vendor_by_territory(territory):
    """Find Technical Survey Executive by territory"""
    if not territory:
        return None
    
    # Find user with Technical Survey Executive role and matching territory
    users = frappe.get_all(
        "User",
        filters={
            "enabled": 1,
            "custom_territory": territory
        },
        fields=["name"]
    )
    
    for user in users:
        if frappe.db.exists("Has Role", {"parent": user.name, "role": "Technical Survey Executive"}):
            return user.name
    
    return None


@frappe.whitelist()
def populate_bom_items(docname, proposed_system_item_code):
    """
    Server-side method to populate ALL BOM items into Technical Survey.
    Stores item_group for dropdown filtering.
    Auto-selects components if only one option per group.
    """
    from solar_erp.solar_erp.api.technical_survey_bom import find_active_bom
    import frappe.utils
    
    # Get the Technical Survey doc
    doc = frappe.get_doc("Technical Survey", docname)
    
    # Find BOM
    bom = find_active_bom(proposed_system_item_code)
    if not bom:
        frappe.throw(_(f"No active BOM found for item {proposed_system_item_code}"))
    
    bom_doc = frappe.get_doc("BOM", bom)
    
    # Update parent fields
    doc.bom_reference = bom
    
    # Clear existing BOM items
    frappe.db.sql("""
        DELETE FROM `tabTechnical BOM Item`
        WHERE parent = %s AND parenttype = 'Technical Survey' AND parentfield = 'bom_other_items'
    """, (docname,))
    
    # Reload doc to clear stale child data
    doc.reload()
    
    # Categorize and store all BOM items
    panels = []
    inverters = []
    batteries = []
    panel_qty_sum = 0
    inverter_qty_sum = 0
    battery_qty_sum = 0
    
    for bom_item in bom_doc.items:
        item_doc = frappe.get_cached_doc("Item", bom_item.item_code)
        item_group = item_doc.item_group
        item_name = item_doc.item_name
        
        # Track component groups
        if item_group == "Panels":
            panels.append(bom_item.item_code)
            panel_qty_sum += bom_item.qty
        elif item_group == "Inverters":
            inverters.append(bom_item.item_code)
            inverter_qty_sum += bom_item.qty
        elif item_group == "Battery":
            batteries.append(bom_item.item_code)
            battery_qty_sum += bom_item.qty
        
        # Append BOM item using Frappe ORM
        doc.append("bom_other_items", {
            "item": bom_item.item_code,
            "item_name": item_name,
            "item_group": item_group,
            "qty": bom_item.qty,
            "uom": bom_item.uom,
            "notes": item_doc.description or ""
        })
    
    # Set quantities
    doc.panel_qty_from_bom = panel_qty_sum
    doc.inverter_qty_from_bom = inverter_qty_sum
    doc.battery_qty_from_bom = battery_qty_sum
    
    # Auto-select component if only one option
    if len(panels) == 1:
        doc.selected_panel = panels[0]
    else:
        doc.selected_panel = None
    
    if len(inverters) == 1:
        doc.selected_inverter = inverters[0]
    else:
        doc.selected_inverter = None
    
    if len(batteries) == 1:
        doc.selected_battery = batteries[0]
    else:
        doc.selected_battery = None
    
    # Save using Frappe ORM
    doc.flags.ignore_mandatory = True
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    
    return {
        "success": True,
        "bom": bom,
        "panels": panels,
        "inverters": inverters,
        "batteries": batteries
    }

