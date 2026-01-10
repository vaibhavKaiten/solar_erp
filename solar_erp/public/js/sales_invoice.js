// Copyright (c) 2025, KaitenSoftware
// Sales Invoice - Advance Payment Collection Button
// Adds action button to collect advance payment from customer using Payment Terms

frappe.ui.form.on('Sales Invoice', {
    refresh: function (frm) {
        add_advance_payment_button(frm);
    }
});


function add_advance_payment_button(frm) {
    // Only show for submitted invoices that are not fully paid
    if (frm.doc.docstatus !== 1) return;
    if (frm.doc.outstanding_amount <= 0) return;

    // Get advance payment info from payment terms
    const advance_info = get_advance_from_payment_terms(frm);

    if (advance_info.advance_percent > 0) {
        frm.add_custom_button(__('Collect Advance Payment'), function () {
            show_advance_payment_dialog(frm, advance_info);
        }, __('Actions')).addClass('btn-primary');
    }
}


function get_advance_from_payment_terms(frm) {
    // Default values
    let advance_info = {
        advance_percent: 0,
        structured_amount: 0,
        payment_term: null,
        due_date: null
    };

    // Check if payment schedule exists
    if (frm.doc.payment_schedule && frm.doc.payment_schedule.length > 0) {
        // Get first payment term (typically the advance)
        const first_term = frm.doc.payment_schedule[0];

        advance_info = {
            advance_percent: first_term.invoice_portion || first_term.payment_amount_percentage || 0,
            structured_amount: first_term.payment_amount || (frm.doc.grand_total * (first_term.invoice_portion / 100)),
            payment_term: first_term.payment_term,
            due_date: first_term.due_date
        };
    }

    return advance_info;
}


function show_advance_payment_dialog(frm, advance_info) {
    const dialog = new frappe.ui.Dialog({
        title: __('Collect Advance Payment'),
        fields: [
            {
                fieldtype: 'Section Break',
                label: __('Payment Terms Info')
            },
            {
                fieldtype: 'Data',
                fieldname: 'payment_term',
                label: __('Payment Term'),
                default: advance_info.payment_term || 'Advance',
                read_only: 1
            },
            {
                fieldtype: 'Percent',
                fieldname: 'advance_percent',
                label: __('Advance %'),
                default: advance_info.advance_percent,
                read_only: 1
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldtype: 'Currency',
                fieldname: 'structured_amount',
                label: __('Structured Advance Amount'),
                default: advance_info.structured_amount,
                read_only: 1,
                description: __('System calculated from Payment Terms')
            },
            {
                fieldtype: 'Section Break',
                label: __('Payment Entry')
            },
            {
                fieldtype: 'Currency',
                fieldname: 'amount_received',
                label: __('Advance Amount Received'),
                default: advance_info.structured_amount,
                reqd: 1,
                description: __('Editable - Enter actual amount received')
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
            // Validate amount received >= structured amount
            if (values.amount_received < advance_info.structured_amount) {
                frappe.msgprint({
                    title: __('Validation Error'),
                    message: __('Advance Amount Received ({0}) must be >= Structured Advance Amount ({1})',
                        [format_currency(values.amount_received, frm.doc.currency),
                        format_currency(advance_info.structured_amount, frm.doc.currency)]),
                    indicator: 'red'
                });
                return;
            }

            dialog.hide();
            create_advance_payment_entry(frm, values, advance_info);
        }
    });

    dialog.show();
}


function create_advance_payment_entry(frm, values, advance_info) {
    frappe.call({
        method: 'solar_erp.solar_erp.api.advance_payment.create_advance_payment_entry',
        args: {
            sales_invoice: frm.doc.name,
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
                    message: __('Payment Entry {0} created successfully', [r.message.payment_entry]),
                    indicator: 'green'
                }, 10);

                // Offer to open Payment Entry
                frappe.confirm(
                    __('Payment Entry {0} created. Do you want to open it?', [r.message.payment_entry]),
                    function () {
                        frappe.set_route('Form', 'Payment Entry', r.message.payment_entry);
                    },
                    function () {
                        frm.reload_doc();
                    }
                );
            }
        }
    });
}
