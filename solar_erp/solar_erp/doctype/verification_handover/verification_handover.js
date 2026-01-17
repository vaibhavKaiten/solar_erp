// Copyright (c) 2025, KaitenSoftware
// Verification Handover Form Controller
// Uses shared execution_common.js for action buttons

frappe.provide('solar_erp.execution');
frappe.ui.form.on('Verification Handover', {
    refresh: function (frm) {
        // Set status indicator
        solar_erp.execution.set_workflow_indicator(frm);

        // Add action buttons based on role and status
        solar_erp.execution.add_action_buttons(frm);

        // Show advance payment status
        solar_erp.execution.show_payment_status(frm);

        
    }
});
