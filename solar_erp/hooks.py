app_name = "solar_erp"
app_title = "Solar ERP"
app_publisher = "KaitenSoftware"
app_description = " Solar Management System"
app_email = "hello@kaitensoftware.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "solar_erp",
# 		"logo": "/assets/solar_erp/logo.png",
# 		"title": "Solar ERP",
# 		"route": "/solar_erp",
# 		"has_permission": "solar_erp.api.permission.has_app_permission"
# 	}
# ]

# hooks.py

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            ["dt", "=", "Lead"]
            
        ]
    },
    {
        "dt": "Customize Form",
        "filters": [
            ["doc_type", "=", "Lead"]
        ]
    },
    {
        "dt": "Custom Field",
        "filters": [
            ["module", "=", "Solar Project"]
        ]
    },

    {
        "dt": "Client Script",
        "filters": [
            ["module", "=", "Solar Project"]
        ]
    },

    {
        "dt": "Server Script",
        "filters": [
            ["module", "=", "Solar Project"]
        ]
    },

    {"doctype": "Workflow State"},
    
    {"doctype": "Workflow", "filters": [["name", "=", "Lead"]]},
    {"doctype":"Workflow Action Master"},

    {
        "dt": "Property Setter",
        "filters": [
            ["module", "=", "Solar Project"]
        ]
    },

    {
        "dt": "Role",
        "filters": [
            ["name", "in", [
                "Sales Executive",
                "Sales Manager",
                "Vendor Executive",
                "Project Manager",
                "Inventory Manager",
                "Purchase Manager",
                "Accounts Manager",
                "Site Visit Manager",
                "Site Visit Vendor Executive",
                "Vendor Manager",
                "Technical Visit Manager",
                "Installation Manager",
                "Loan Process Executive",
                "Subsidy Executive",
                "Installation Vendor Manager",
                "Installation Vendor Executive",
                "Technical Visit Vendor Manager",
                "Site Visit Vendor Manager",
                "Discom Executive",
                "Vendor Field Staff",
                "Service Head",
                "Service Executive",
                "Technical Visit Vendor Executive",
                "Lead Manager",
                "Lead Executive",
                "Panel Installation Executive",
                "Panel Installation Manager",
                "Meter Installation Executive",
                "Meter Installation Manager",
                "Technical Survey Executive",
                "Technical Survey Manager"
            ]]
        ]
    },

    # Lead customizations from separate JSON file
    # "solar_erp/solar_project/custom/lead.json"
]


# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/solar_erp/css/solar_erp.css"
# app_include_js = "/assets/solar_erp/js/execution_common.js"
app_include_js = "public/js/execution_common.js"

# include js, css files in header of web template
# web_include_css = "/assets/solar_erp/css/solar_erp.css"
# web_include_js = "/assets/solar_erp/js/solar_erp.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "solar_erp/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Quotation": "public/js/quotation.js",
    "Sales Invoice": "public/js/sales_invoice.js",
    "Lead": "public/js/lead.js",
    "Sales Order": "public/js/sales_order_mr.js",
    "Material Request": "public/js/material_request_gst.js",
    "Supplier": "public/js/supplier.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "solar_erp/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "solar_erp.utils.jinja_methods",
# 	"filters": "solar_erp.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "solar_erp.install.before_install"
# after_install = "solar_erp.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "solar_erp.uninstall.before_uninstall"
# after_uninstall = "solar_erp.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "solar_erp.utils.before_app_install"
# after_app_install = "solar_erp.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "solar_erp.utils.before_app_uninstall"
# after_app_uninstall = "solar_erp.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "solar_erp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

permission_query_conditions = {
	"Technical Survey": "solar_erp.solar_erp.permissions.technical_survey_permissions.get_permission_query_conditions",
}

has_permission = {
	"Technical Survey": "solar_erp.solar_erp.permissions.technical_survey_permissions.has_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Lead": {
        "validate": "solar_erp.solar_erp.doc_events.lead_events.validate",
        "on_update": "solar_erp.solar_erp.doc_events.lead_events.on_update"
    },
    "Contact": {
        "after_insert": "solar_erp.solar_erp.doc_events.contact_events.auto_link_contact_to_supplier",
        "on_update": "solar_erp.solar_erp.doc_events.contact_events.auto_link_contact_to_supplier"
    },
    "User": {
        "on_update": "solar_erp.solar_erp.doc_events.contact_events.link_contact_on_user_role_change"
    },
    "Quotation": {
        "on_submit": "solar_erp.solar_erp.api.quotation_workflow.on_quotation_submit"
    },
    "Payment Entry": {
        "on_submit": "solar_erp.solar_erp.api.advance_payment.on_payment_entry_submit"
    },
    "Sales Order": {
        "on_submit": "solar_erp.solar_erp.api.bom_stock_reservation.on_sales_order_submit",
        "on_cancel": "solar_erp.solar_erp.api.bom_stock_reservation.on_sales_order_cancel"
    },
    "Delivery Note": {
        "on_submit": "solar_erp.solar_erp.doc_events.delivery_note_events.on_submit"
    },
    "Purchase Receipt": {
        "on_submit": "solar_erp.solar_erp.api.bom_stock_reservation.on_purchase_receipt_submit"
    },
    "Material Request": {
        # REMOVED: Hard lock on manual Material Request creation
        # "before_insert": "solar_erp.solar_erp.api.material_request_validation.validate_material_request",
        "on_submit": "solar_erp.solar_erp.api.material_request_validation.on_material_request_submit"
    },
    "Purchase Order": {
        "validate": "solar_erp.solar_erp.api.purchase_gst_hook.apply_item_wise_taxes"
    },
    # Execution DocTypes - Workflow Validation & Vendor Continuity
    "Technical Survey": {
        "before_insert": "solar_erp.solar_erp.api.execution_workflow.validate_execution_stage",
        "validate": "solar_erp.solar_erp.api.execution_workflow.auto_assign_vendor",
        "on_trash": "solar_erp.solar_erp.permissions.technical_survey_permissions.on_trash"
    },
    "Structure Mounting": {
        "before_insert": "solar_erp.solar_erp.api.execution_workflow.validate_execution_stage",
        "validate": "solar_erp.solar_erp.api.execution_workflow.auto_assign_vendor"
    },
    "Panel Installation": {
        "before_insert": "solar_erp.solar_erp.api.execution_workflow.validate_execution_stage",
        "validate": "solar_erp.solar_erp.api.execution_workflow.auto_assign_vendor"
    },
    "Meter Installation": {
        "before_insert": "solar_erp.solar_erp.api.execution_workflow.validate_execution_stage",
        "validate": "solar_erp.solar_erp.api.execution_workflow.auto_assign_vendor"
    },
    "Meter Commissioning": {
        "before_insert": "solar_erp.solar_erp.api.execution_workflow.validate_execution_stage",
        "validate": "solar_erp.solar_erp.api.execution_workflow.auto_assign_vendor"
    },
    "Verification Handover": {
        "before_insert": "solar_erp.solar_erp.api.execution_workflow.validate_execution_stage",
        "validate": "solar_erp.solar_erp.api.execution_workflow.auto_assign_vendor"
    }
}


# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"solar_erp.solar_project.tasks.cleanup_disabled_vendor_users"
	]
}

# Testing
# -------

# before_tests = "solar_erp.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "solar_erp.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "solar_erp.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["solar_erp.utils.before_request"]
# after_request = ["solar_erp.utils.after_request"]

# Job Events
# ----------
# before_job = ["solar_erp.utils.before_job"]
# after_job = ["solar_erp.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"solar_erp.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

