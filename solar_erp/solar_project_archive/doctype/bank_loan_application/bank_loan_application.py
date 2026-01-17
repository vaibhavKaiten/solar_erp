# -*- coding: utf-8 -*-
# Copyright (c) 2025, Solar ERP
# License: MIT

import frappe
from frappe.model.document import Document

class BankLoanApplication(Document):
    def before_save(self):
        # Auto-fetch K-Number from Lead if available
        if self.lead and not self.k_number:
            lead = frappe.get_doc('Lead', self.lead)
            if hasattr(lead, 'custom_k_number'):
                self.k_number = lead.custom_k_number
            elif hasattr(lead, 'k_number'):
                self.k_number = lead.k_number
    
    def validate(self):
        # Ensure required fields based on workflow state
        if hasattr(self, 'workflow_state') and self.workflow_state:
            if self.workflow_state in ['Submitted', 'Under Review', 'Approved']:
                if not self.first_name:
                    frappe.throw('First Name is required')
                if not self.mobile_no:
                    frappe.throw('Mobile No is required')
                if not self.system_capacity_kw:
                    frappe.throw('System Capacity (KW) is required')
