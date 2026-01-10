// Copyright (c) 2025, KaitenSoftware
// Meter Commissioning Form Controller
// Uses shared execution_common.js for action buttons

frappe.ui.form.on('Meter Commissioning', {
    refresh: function (frm) {
        // Set status indicator
        solar_erp.execution.set_status_indicator(frm);

        // Add action buttons based on role and status
        solar_erp.execution.add_action_buttons(frm);

        // Show advance payment status
        solar_erp.execution.show_payment_status(frm);
    }
});
