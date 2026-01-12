#!/usr/bin/env python3
# Copyright (c) 2026, Kaiten Software and contributors
# For license information, please see license.txt

"""
Add custom_consolidated field to Material Request DocType
This field allows marking Material Requests as consolidated for planning
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def add_consolidated_field():
	"""
	Add custom_consolidated field to Material Request
	
	Field Properties:
	- Fieldname: custom_consolidated
	- Label: Consolidated
	- Fieldtype: Check
	- Allow On Submit: Yes (editable on submitted documents)
	- Read Only: No
	"""
	
	custom_fields = {
		"Material Request": [
			{
				"fieldname": "custom_consolidated",
				"label": "Consolidated",
				"fieldtype": "Check",
				"insert_after": "status",
				"default": 0,
				"read_only": 0,
				"allow_on_submit": 0,  # CRITICAL: Must be 1 to allow editing on submitted docs
				"description": "Indicates if this Material Request has been consolidated for procurement planning",
				"no_copy": 1
			}
		]
	}
	
	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()
	
	print("✓ custom_consolidated field added/updated successfully")
	print("  - Allow On Submit: 1 (editable on submitted documents)")
	print("  - Read Only: 0 (editable)")


if __name__ == "__main__":
	add_consolidated_field()
