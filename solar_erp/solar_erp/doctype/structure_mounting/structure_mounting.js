// Copyright (c) 2025, KaitenSoftware
// Structure Mounting Form Controller
// Uses shared execution_common.js for action buttons

frappe.provide('solar_erp.execution');

frappe.ui.form.on('Structure Mounting', {
    refresh: function (frm) {
        // Set status indicator
        solar_erp.execution.set_status_indicator(frm);

        // Add action buttons based on role and status
        solar_erp.execution.add_action_buttons(frm);

        // Show advance payment status
        solar_erp.execution.show_payment_status(frm);

        // Initiate Structure Mounting Button
        if (frm.doc.status === 'Draft' && !frm.is_new()) {
            // Visible to Admin, System Manager, Project Manager, Structure Mounting Manager
            if (frappe.user.has_role('System Manager') ||
                frappe.user.has_role('Administrator') ||
                frappe.user.has_role('Project Manager') ||
                frappe.user.has_role('Structure Mounting Manager')) {

                // Add as a primary inner button (not in assignment menu) for visibility
                frm.add_custom_button(__('Initiate Structure Mounting'), function () {
                    frappe.call({
                        method: 'solar_erp.solar_erp.doctype.structure_mounting.structure_mounting.initiate_structure_mounting',
                        args: { docname: frm.doc.name },
                        freeze: true,
                        freeze_message: __('Initiating Structure Mounting...'),
                        callback: function (r) {
                            if (!r.exc) {
                                frm.reload_doc();
                            }
                        }
                    });
                }).addClass('btn-primary');
            }
        }

    }
});

