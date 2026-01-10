// Copyright (c) 2025, Solar ERP
// Quotation Workflow - Status-based action buttons
// Status Flow: Draft → Open → Advance Pending / Revised / Rejected

frappe.ui.form.on('Quotation', {
    refresh: function (frm) {
        add_quotation_actions(frm);
        set_quotation_indicator(frm);
        apply_lock_rules(frm);
    },

    before_submit: function (frm) {
        // On submit, if status is Draft, change to Submitted
        if (frm.doc.custom_quotation_status === 'Draft' || !frm.doc.custom_quotation_status) {
            frm.set_value('custom_quotation_status', 'Submitted');
        }
    }
});


function add_quotation_actions(frm) {
    if (frm.is_new()) return;

    // Clear custom buttons
    frm.clear_custom_buttons();

    const status = frm.doc.custom_quotation_status || 'Draft';
    const is_sales_manager = frappe.user.has_role('Sales Manager');
    const is_admin = frappe.user.has_role('System Manager') || frappe.user.has_role('Administrator');

    // =================================================================
    // STATUS: DRAFT - Only Save/Submit visible (standard Frappe buttons)
    // No commercial action buttons
    // =================================================================
    if (status === 'Draft') {
        // No custom action buttons for Draft
        // Standard Save/Submit buttons are handled by Frappe
        return;
    }

    // =================================================================
    // STATUS: SUBMITTED - Advance Payment and Sales Invoice buttons
    // =================================================================
    if (status === 'Submitted') {
        // Collect Advance Payment
        frm.add_custom_button(__('Advance Payment'), function () {
            show_advance_payment_dialog(frm);
        }, __('Create')).addClass('btn-primary');

        // Create Sales Invoice
        frm.add_custom_button(__('Advance Sales Invoice'), function () {
            create_sales_invoice_from_quotation(frm);
        }, __('Create'));
        return;
    }

    // =================================================================
    // STATUS: ADVANCE APPROVED - Sales Order can now be created
    // BOM is fetched from approved Technical Survey
    // =================================================================
    if (status === 'Advance Approved') {
        // Create Sales Order (with BOM from Technical Survey)
        frm.add_custom_button(__('Sales Order'), function () {
            create_sales_order_from_survey(frm);
        }, __('Create')).addClass('btn-success');

        // Also allow viewing the linked Technical Survey
        if (frm.doc.custom_technical_survey) {
            frm.add_custom_button(__('View Technical Survey'), function () {
                frappe.set_route('Form', 'Technical Survey', frm.doc.custom_technical_survey);
            }, __('Links'));
        }
        return;
    }

    // =================================================================
    // STATUS: ADVANCE PENDING - Advance Payment, Sales Invoice
    // NO: Sales Order (until Advance Verified)
    // =================================================================
    if (status === 'Advance Pending') {
        // Collect Advance Payment
        frm.add_custom_button(__('Advance Payment'), function () {
            show_advance_payment_dialog(frm);
        }, __('Create')).addClass('btn-primary');

        // Create Sales Invoice
        frm.add_custom_button(__('Advance Sales Invoice'), function () {
            create_sales_invoice_from_quotation(frm);
        }, __('Create'));

        // Sales Order button - HIDDEN until Advance Verified
        // (This is handled by existing logic - do NOT show here)
        return;
    }

    // =================================================================
    // STATUS: REVISED - Lock old version, no actions
    // =================================================================
    if (status === 'Revised') {
        frm.dashboard.add_comment(__('This quotation has been revised. A new version was created.'), 'yellow', true);
        return;
    }

    // =================================================================
    // STATUS: REJECTED - No actions allowed
    // =================================================================
    if (status === 'Rejected') {
        frm.dashboard.add_comment(__('This quotation was rejected by the customer.'), 'red', true);
        return;
    }

    // Link to Technical Survey if available
    if (frm.doc.custom_technical_survey) {
        frm.add_custom_button(__('View Technical Survey'), function () {
            frappe.set_route('Form', 'Technical Survey', frm.doc.custom_technical_survey);
        }, __('Links'));
    }
}


// Create Sales Invoice from Quotation
function create_sales_invoice_from_quotation(frm) {
    frappe.model.open_mapped_doc({
        method: "erpnext.selling.doctype.quotation.quotation.make_sales_invoice",
        frm: frm
    });
}


// Create Sales Order from Quotation with BOM from Technical Survey
function create_sales_order_from_survey(frm) {
    // First check if we can create Sales Order
    frappe.call({
        method: 'solar_erp.solar_erp.api.sales_order_bom.check_can_make_sales_order',
        args: {
            quotation_name: frm.doc.name
        },
        callback: function (r) {
            if (r.message) {
                if (r.message.can_create) {
                    // Proceed with Sales Order creation
                    frappe.confirm(
                        __('Create Sales Order from this Quotation?<br><br>' +
                            'BOM will be fetched from Technical Survey: <b>{0}</b><br>' +
                            'This BOM will be locked and used for stock reservation.', [r.message.technical_survey]),
                        function () {
                            // Confirmed
                            frappe.call({
                                method: 'solar_erp.solar_erp.api.sales_order_bom.make_sales_order_from_quotation',
                                args: {
                                    source_name: frm.doc.name
                                },
                                freeze: true,
                                freeze_message: __('Creating Sales Order with BOM...'),
                                callback: function (res) {
                                    if (res.message) {
                                        frappe.show_alert({
                                            message: __('Sales Order {0} created', [res.message.name]),
                                            indicator: 'green'
                                        }, 10);
                                        frappe.set_route('Form', 'Sales Order', res.message.name);
                                    }
                                }
                            });
                        }
                    );
                } else {
                    frappe.msgprint({
                        title: __('Cannot Create Sales Order'),
                        message: r.message.message,
                        indicator: 'red'
                    });
                }
            }
        }
    });
}


// =============================================================================
// ADVANCE PAYMENT FUNCTIONS
// =============================================================================

function show_advance_payment_dialog(frm) {
    frappe.call({
        method: 'solar_erp.solar_erp.api.advance_payment.get_advance_info_from_quotation',
        args: {
            quotation: frm.doc.name,
            payment_terms_template: 'payment procedure'
        },
        callback: function (r) {
            if (r.message) {
                open_advance_dialog(frm, r.message);
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Could not fetch payment terms. Please ensure "payment procedure" template exists.'),
                    indicator: 'red'
                });
            }
        }
    });
}


function open_advance_dialog(frm, advance_info) {
    const dialog = new frappe.ui.Dialog({
        title: __('Collect Advance Payment'),
        fields: [
            {
                fieldtype: 'Section Break',
                label: __('Payment Terms Info (Read-Only)')
            },
            {
                fieldtype: 'Data',
                fieldname: 'payment_terms_template',
                label: __('Payment Terms Template'),
                default: advance_info.payment_terms_template || 'payment procedure',
                read_only: 1
            },
            {
                fieldtype: 'Data',
                fieldname: 'payment_term',
                label: __('Payment Term'),
                default: advance_info.payment_term || 'Advance',
                read_only: 1
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Percent',
                fieldname: 'advance_percent',
                label: __('Advance %'),
                default: advance_info.advance_percent || 0,
                read_only: 1
            },
            {
                fieldtype: 'Currency',
                fieldname: 'structured_amount',
                label: __('Structured Advance Amount'),
                default: advance_info.structured_amount || 0,
                read_only: 1,
                description: __('Auto-calculated: Grand Total × Advance %')
            },
            {
                fieldtype: 'Section Break',
                label: __('Payment Details')
            },
            {
                fieldtype: 'Currency',
                fieldname: 'amount_received',
                label: __('Advance Amount Received'),
                default: advance_info.structured_amount || 0,
                reqd: 1
            },
            {
                fieldtype: 'Link',
                fieldname: 'mode_of_payment',
                label: __('Mode of Payment'),
                options: 'Mode of Payment',
                reqd: 1
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Data',
                fieldname: 'reference_no',
                label: __('Reference / Cheque No')
            },
            {
                fieldtype: 'Date',
                fieldname: 'reference_date',
                label: __('Reference Date'),
                default: frappe.datetime.get_today()
            }
        ],
        primary_action_label: __('Create Payment Entry'),
        primary_action: function (values) {
            dialog.hide();
            create_quotation_advance_payment(frm, values, advance_info);
        }
    });

    dialog.show();
}


function create_quotation_advance_payment(frm, values, advance_info) {
    frappe.call({
        method: 'solar_erp.solar_erp.api.advance_payment.create_advance_payment_from_quotation',
        args: {
            quotation: frm.doc.name,
            amount: values.amount_received,
            mode_of_payment: values.mode_of_payment,
            reference_no: values.reference_no || '',
            reference_date: values.reference_date || '',
            payment_term: advance_info.payment_term || '',
            structured_amount: advance_info.structured_amount,
            advance_percent: advance_info.advance_percent
        },
        freeze: true,
        freeze_message: __('Creating Payment Entry...'),
        callback: function (r) {
            if (r.message && r.message.status === 'success') {
                frappe.show_alert({
                    message: __('Payment Entry {0} created', [r.message.payment_entry]),
                    indicator: 'green'
                }, 10);
                frm.reload_doc();
            }
        }
    });
}


// =============================================================================
// STATUS INDICATOR
// =============================================================================

function set_quotation_indicator(frm) {
    const status = frm.doc.custom_quotation_status || 'Draft';
    const status_colors = {
        'Draft': 'grey',
        'Submitted': 'green',
        'Advance Approved': 'blue',
        'Advance Pending': 'orange',
        'Revised': 'yellow',
        'Rejected': 'red'
    };

    const color = status_colors[status] || 'grey';
    frm.page.set_indicator(status, color);
}


// =============================================================================
// LOCK RULES
// =============================================================================

function apply_lock_rules(frm) {
    const status = frm.doc.custom_quotation_status || 'Draft';
    const is_admin = frappe.user.has_role('System Manager') || frappe.user.has_role('Administrator');

    // Draft - fully editable
    if (status === 'Draft') {
        return;
    }

    // Open - pricing frozen but can still be saved
    if (status === 'Open') {
        // Disable price editing on items
        if (frm.fields_dict['items']) {
            frm.fields_dict['items'].grid.update_docfield_property('rate', 'read_only', 1);
            frm.fields_dict['items'].grid.update_docfield_property('price_list_rate', 'read_only', 1);
            frm.fields_dict['items'].grid.update_docfield_property('discount_percentage', 'read_only', 1);
            frm.fields_dict['items'].grid.update_docfield_property('discount_amount', 'read_only', 1);
        }
        return;
    }

    // Advance Pending, Revised, Rejected - fully locked
    if (['Advance Pending', 'Revised', 'Rejected'].includes(status)) {
        frm.disable_save();
        if (!is_admin) {
            frm.set_read_only();
        }
    }
}
