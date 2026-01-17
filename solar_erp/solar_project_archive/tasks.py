# Copyright (c) 2025, Kaiten Software and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import add_days, nowdate, getdate


def cleanup_disabled_vendor_users():
	"""
	Delete vendor staff users who have been disabled for more than 90 days.
	Runs daily via scheduler.
	"""
	try:
		# Calculate the cutoff date (90 days ago)
		cutoff_date = add_days(nowdate(), -90)
		
		# Get all vendor users who are disabled and have custom_vendor_reference
		disabled_users = frappe.get_all(
			"User",
			filters={
				"enabled": 0,
				"custom_vendor_reference": ["!=", ""],
				"custom_disabled_date": ["<=", cutoff_date]
			},
			fields=["name", "email", "custom_vendor_reference", "custom_disabled_date"]
		)
		
		deleted_count = 0
		
		for user in disabled_users:
			try:
				# Calculate days since disabled
				if user.custom_disabled_date:
					days_disabled = (getdate(nowdate()) - getdate(user.custom_disabled_date)).days
				else:
					# Fallback: if no disabled_date, skip this user
					continue
				
				if days_disabled >= 90:
					# Delete the user
					frappe.delete_doc("User", user.name, ignore_permissions=True, force=True)
					deleted_count += 1
					
					frappe.logger().info(
						f"Deleted vendor user {user.email} from vendor {user.custom_vendor_reference} (disabled for {days_disabled} days)"
					)
			
			except Exception as e:
				frappe.logger().error(
					f"Error deleting vendor user {user.get('email', user.name)}: {str(e)}"
				)
				continue
		
		if deleted_count > 0:
			frappe.db.commit()
			frappe.logger().info(
				f"Cleanup completed: Deleted {deleted_count} vendor user(s) disabled for 90+ days"
			)
		else:
			frappe.logger().info("Cleanup completed: No vendor users to delete")
	
	except Exception as e:
		frappe.logger().error(f"Error in cleanup_disabled_vendor_users: {str(e)}")
		frappe.db.rollback()
