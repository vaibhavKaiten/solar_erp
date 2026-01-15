/**
 * Custom Assignment Filter for Solar ERP Doctypes
 * Filters "Assigned To" users based on assigned_vendor's Vendor Executives
 */

frappe.provide('solar_erp.assignment');

// Doctypes that use custom assignment filtering
solar_erp.assignment.EXECUTION_DOCTYPES = [
    "Meter Commissioning",
    "Meter Installation",
    "Project Installation",
    "Structure Mounting",
    "Technical Survey",
    "Verification Handover"
];

/**
 * Override the assign_to method globally for our doctypes
 */
$(document).on('app_ready', function() {
    // Store the original assign_to.add method
    const original_assign_to_add = frappe.ui.form.AssignTo.prototype.add;
    
    // Override the add method
    frappe.ui.form.AssignTo.prototype.add = function() {
        const me = this;
        const frm = this.frm;
        
        // Check if this is one of our execution doctypes
        if (solar_erp.assignment.EXECUTION_DOCTYPES.includes(frm.doctype)) {
            const assigned_vendor = frm.doc.assigned_vendor;
            
            if (assigned_vendor) {
                // Use custom assignment dialog with filtered users
                solar_erp.assignment.show_custom_assign_dialog(frm, assigned_vendor);
                return;
            }
        }
        
        // For all other cases, use the original method
        original_assign_to_add.call(me);
    };
});

/**
 * Show custom assignment dialog with filtered users
 */
solar_erp.assignment.show_custom_assign_dialog = function(frm, assigned_vendor) {
    // First, fetch the vendor executives
    frappe.call({
        method: 'solar_erp.solar_erp.api.assignment_filter.get_vendor_executives',
        args: {
            vendor: assigned_vendor
        },
        callback: (r) => {
            if (r.message && r.message.length > 0) {
                const users = r.message;
                
                // Create a custom dialog
                const d = new frappe.ui.Dialog({
                    title: __('Add to ToDo'),
                    fields: [
                        {
                            fieldtype: 'Select',
                            fieldname: 'assign_to',
                            label: __('Assign To'),
                            options: users,
                            reqd: 1,
                            description: __(  `Filtered to show only Vendor Executives from ${assigned_vendor}`)
                        },
                        {
                            fieldtype: 'Section Break'
                        },
                        {
                            fieldtype: 'Small Text',
                            fieldname: 'description',
                            label: __('Comment')
                        },
                        {
                            fieldtype: 'Section Break'
                        },
                        {
                            fieldtype: 'Column Break'
                        },
                        {
                            fieldtype: 'Date',
                            fieldname: 'date',
                            label: __('Complete By')
                        },
                        {
                            fieldtype: 'Column Break'
                        },
                        {
                            fieldtype: 'Select',
                            fieldname: 'priority',
                            label: __('Priority'),
                            options: [
                                {label: __('Low'), value: 'Low'},
                                {label: __('Medium'), value: 'Medium'},
                                {label: __('High'), value: 'High'}
                            ],
                            'default': 'Medium'
                        },
                        {
                            fieldtype: 'Section Break'
                        },
                        {
                            fieldtype: 'Check',
                            fieldname: 'notify',
                            label: __('Notify by Email'),
                            'default': 1
                        }
                    ],
                    primary_action_label: __('Add'),
                    primary_action: function() {
                        const values = d.get_values();
                        
                        if (!values) return;
                        
                        d.hide();
                        
                        frappe.call({
                            method: 'frappe.desk.form.assign_to.add',
                            args: {
                                doctype: frm.doctype,
                                name: frm.doc.name,
                                assign_to: [values.assign_to],
                                description: values.description,
                                date: values.date,
                                priority: values.priority,
                                notify: values.notify
                            },
                            callback: function(r) {
                                if (!r.exc) {
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                });
                
                d.show();
            } else {
                frappe.msgprint({
                    title: __('No Users Found'),
                    message: __('No Vendor Executives found for the assigned vendor: {0}. Cannot assign task.', [assigned_vendor]),
                    indicator: 'orange'
                });
            }
        },
        error: (err) => {
            console.error("Error fetching vendor executives:", err);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to fetch vendor executives. Please try again.'),
                indicator: 'red'
            });
        }
    });
};
