# Copyright (c) 2026, Kaiten Software and contributors
# For license information, please see license.txt

"""
Custom fields for Material Request DocType
to support Procurement Consolidation workflow
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_material_request_custom_fields():
	"""
	Create custom fields for Material Request to track consolidation status
	
	Fields:
	- custom_consolidated: Check field to mark MR as consolidated
	"""
	
	custom_fields = {
		"Material Request": [
			{
				"fieldname": "custom_consolidated",
				"label": "Consolidated",
				"fieldtype": "Check",
				"default": "0",
				"insert_after": "status",
				"read_only": 0,
				"description": "Indicates if this Material Request has been consolidated in a Procurement Consolidation document",
				"allow_on_submit": 0,  # Field is read-only on submitted documents
				"no_copy": 1
			}
		]
	}
	
	create_custom_fields(custom_fields, update=True)
	frappe.db.commit()
	
	print("✓ Material Request custom fields created successfully")


if __name__ == "__main__":
	create_material_request_custom_fields()
