// Copyright (c) 2025, KaitenSoftware
// Technical Survey Form Controller
// Uses shared execution_common.js for action buttons + BOM functionality

frappe.ui.form.on('Technical Survey', {
    setup: function (frm) {
        frm.set_query('proposed_system', function () {
            return {
                filters: {
                    item_group: 'Products',

                    is_sales_item: 1,
                    disabled: 0
                }
            };
        });

        setup_filters(frm);
    },

    onload: function (frm) {
        // BOM data is now stored, filters setup automatically in setup()
    },

    refresh: function (frm) {
        // Set status indicator
        set_status_indicator(frm);

        // Add workflow action buttons
        add_workflow_action_buttons(frm);

        // Add View Quotation link if approved
        add_quotation_link(frm);

        // Add Initiate Technical Survey button for System Manager/Administrator
        add_initiate_survey_button(frm);

        // Filter assigned_internal_user to show only vendor executives from assigned vendor company
        if (frm.doc.assigned_vendor) {
            frm.set_query('assigned_internal_user', function () {
                return {
                    query: 'solar_erp.solar_erp.queries.get_vendor_executives',
                    filters: {
                        'vendor_company': frm.doc.assigned_vendor
                    }
                };
            });

            // Also filter custom_technical_executive if it exists
            frm.set_query('custom_technical_executive', function () {
                return {
                    query: 'solar_erp.solar_erp.queries.get_vendor_executives',
                    filters: {
                        'vendor_company': frm.doc.assigned_vendor
                    }
                };
            });

            // Make custom_technical_executive visible to vendor managers
            if (frappe.user.has_role('Vendor Manager')) {
                frm.set_df_property('custom_technical_executive', 'hidden', 0);
                frm.set_df_property('custom_technical_executive', 'read_only', 0);
            }
        }
    },

    proposed_system: function (frm) {
        if (frm.doc.proposed_system) {
            populate_bom_from_proposed_system(frm);
        } else {
            clear_bom_fields(frm);
        }
    }
});


// =============================================================================
// QUOTATION LINK (TS-specific)
// =============================================================================
function add_quotation_link(frm) {
    if (frm.is_new()) return;

    const status = frm.doc.status;
    const is_admin = frappe.user.has_role('System Manager') || frappe.user.has_role('Administrator');
    const is_sales_manager = frappe.user.has_role('Sales Manager');

    if ((is_sales_manager || is_admin) && status === 'Approved') {
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Quotation',
                filters: { custom_technical_survey: frm.doc.name },
                fieldname: 'name'
            },
            callback: function (r) {
                if (r.message && r.message.name) {
                    // 🚀 Direct “View Quotation” button — no dropdown
                    frm.add_custom_button(__('View Quotation'), function () {
                        frappe.set_route('Form', 'Quotation', r.message.name);
                    }).addClass('btn-primary');
                }
            }
        });
    }
}



// =============================================================================
// WORKFLOW ACTION BUTTONS
// =============================================================================

function add_workflow_action_buttons(frm) {
    if (frm.is_new()) return;

    frm.clear_custom_buttons();

    const status = frm.doc.status;
    const is_system_manager = frappe.user.has_role('System Manager');
    const is_administrator = frappe.user.has_role('Administrator');
    const is_vendor_executive = frappe.user.has_role('Vendor Executive');
    const is_vendor_manager = frappe.user.has_role('Vendor Manager');
    const is_execution_manager = frappe.user.has_role('Execution Manager');

    // 1. Send to Vendor (Solar Company - System Manager)
    if ((is_system_manager || is_administrator) && status === 'Draft' && frm.doc.assigned_vendor) {
        frm.add_custom_button(__('Send to Vendor'), function () {
            frappe.confirm(
                __('Send this Technical Survey to vendor {0}?', [frm.doc.assigned_vendor]),
                function () {
                    frappe.call({
                        method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.send_to_vendor',
                        args: { docname: frm.doc.name },
                        callback: function (r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.show_alert({ message: r.message.message, indicator: 'green' });
                                frm.reload_doc();
                            }
                        }
                    });
                }
            );
        }, __('Actions')).addClass('btn-primary');
    }

    // 2. Start (Vendor Executive)
    if (is_vendor_executive && (status === 'Assigned' || status === 'Scheduled' || status === 'Reopened')) {
        frm.add_custom_button(__('Start'), function () {
            frappe.call({
                method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.start_work',
                args: { docname: frm.doc.name },
                callback: function (r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({ message: r.message.message, indicator: 'green' });
                        frm.reload_doc();
                    }
                }
            });
        }, __('Actions')).addClass('btn-primary');
    }

    // 3. Put on Hold (Vendor Executive/Manager)
    if ((is_vendor_executive || is_vendor_manager) && (status === 'Assigned' || status === 'In Progress')) {
        frm.add_custom_button(__('Put on Hold'), function () {
            frappe.prompt({
                fieldtype: 'Small Text',
                label: __('Reason for Hold'),
                fieldname: 'reason',
                reqd: 1
            }, function (values) {
                frappe.call({
                    method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.hold_work',
                    args: {
                        docname: frm.doc.name,
                        reason: values.reason
                    },
                    callback: function (r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.show_alert({ message: r.message.message, indicator: 'orange' });
                            frm.reload_doc();
                        }
                    }
                });
            }, __('Put on Hold'), __('Submit'));
        }, __('Actions')).addClass('btn-warning');
    }

    // 4. Submit (Vendor Executive)
    if (is_vendor_executive && status === 'In Progress') {
        frm.add_custom_button(__('Submit for Review'), function () {
            frappe.confirm(
                __('Submit this survey for review? You will not be able to edit after submission.'),
                function () {
                    frappe.call({
                        method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.submit_survey',
                        args: { docname: frm.doc.name },
                        callback: function (r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.show_alert({ message: r.message.message, indicator: 'green' });
                                frm.reload_doc();
                            }
                        }
                    });
                }
            );
        }, __('Actions')).addClass('btn-success');
    }

    // 5. Complete (Vendor Manager)
    if (is_vendor_manager && status === 'In Review') {
        frm.add_custom_button(__('Complete'), function () {
            frappe.confirm(
                __('Mark this survey as completed?'),
                function () {
                    frappe.call({
                        method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.complete_survey',
                        args: { docname: frm.doc.name },
                        callback: function (r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.show_alert({ message: r.message.message, indicator: 'green' });
                                frm.reload_doc();
                            }
                        }
                    });
                }
            );
        }, __('Actions')).addClass('btn-success');
    }

    // 6. Reject (Vendor Manager or Execution Manager)
    if ((is_vendor_manager || is_execution_manager) && status !== 'Rejected' && status !== 'Approved') {
        frm.add_custom_button(__('Reject'), function () {
            frappe.prompt({
                fieldtype: 'Small Text',
                label: __('Reason for Rejection'),
                fieldname: 'reason',
                reqd: 1
            }, function (values) {
                frappe.call({
                    method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.reject_survey',
                    args: {
                        docname: frm.doc.name,
                        reason: values.reason
                    },
                    callback: function (r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.show_alert({ message: r.message.message, indicator: 'red' });
                            frm.reload_doc();
                        }
                    }
                });
            }, __('Reject Survey'), __('Reject'));
        }, __('Actions')).addClass('btn-danger');
    }

    // 7. Rework (Vendor Manager or Execution Manager)
    if ((is_vendor_manager || is_execution_manager) && (status === 'Completed' || status === 'Rejected' || status === 'In Review')) {
        frm.add_custom_button(__('Rework'), function () {
            frappe.prompt({
                fieldtype: 'Small Text',
                label: __('Reason for Rework'),
                fieldname: 'reason',
                reqd: 1
            }, function (values) {
                frappe.call({
                    method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.rework_survey',
                    args: {
                        docname: frm.doc.name,
                        reason: values.reason
                    },
                    callback: function (r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.show_alert({ message: r.message.message, indicator: 'orange' });
                            frm.reload_doc();
                        }
                    }
                });
            }, __('Request Rework'), __('Submit'));
        }, __('Actions')).addClass('btn-warning');
    }

    // 8. Approve (Execution Manager)
    if (is_execution_manager && status === 'Completed') {
        frm.add_custom_button(__('Approve'), function () {
            frappe.prompt({
                fieldtype: 'Small Text',
                label: __('Approval Comment'),
                fieldname: 'comment',
                reqd: 1
            }, function (values) {
                frappe.call({
                    method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.approve_survey',
                    args: {
                        docname: frm.doc.name,
                        comment: values.comment
                    },
                    callback: function (r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.show_alert({ message: r.message.message, indicator: 'green' });

                            // Show quotation creation notification
                            if (r.message.quotation_created && r.message.quotation_name) {
                                frappe.show_alert({
                                    message: __('Quotation {0} created successfully. <a href="/app/quotation/{0}">Click to open</a>', [r.message.quotation_name]),
                                    indicator: 'blue'
                                }, 30);
                            }

                            frm.reload_doc();
                        }
                    }
                });
            }, __('Approve Survey'), __('Approve'));
        }, __('Actions')).addClass('btn-success');
    }
}


// =============================================================================
// STATUS INDICATOR
// =============================================================================

function set_status_indicator(frm) {
    const status_colors = {
        'Draft': 'grey',
        'Assigned': 'blue',
        'In Progress': 'orange',
        'On Hold': 'yellow',
        'In Review': 'purple',
        'Completed': 'cyan',
        'Approved': 'green',
        'Rejected': 'red',
        'Scheduled': 'blue',
        'Reopened': 'cyan',
        'Closed': 'red'
    };

    const color = status_colors[frm.doc.status] || 'grey';
    frm.page.set_indicator(frm.doc.status, color);
}


// =============================================================================
// BOM FUNCTIONS (Keeping existing functionality)
// =============================================================================

// The old add_action_buttons and set_status_indicator are no longer needed
// as we now use custom workflow buttons

function add_action_buttons(frm) {
    // DEPRECATED - Using solar_erp.execution.add_action_buttons instead
    // Keeping empty function to prevent errors from any lingering calls
    frm.clear_custom_buttons();

    // Check user roles
    const is_executive = frappe.user.has_role('Technical Survey Executive');
    const is_manager = frappe.user.has_role('Technical Survey Manager');
    const is_admin = frappe.user.has_role('System Manager') || frappe.user.has_role('Administrator');

    const status = frm.doc.status;

    // EXECUTIVE ACTIONS
    if (is_executive || is_admin) {
        // Start button - Scheduled, Reopened -> In Progress
        if (status === 'Scheduled' || status === 'Reopened') {
            frm.add_custom_button(__('Start'), function () {
                frappe.call({
                    method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.start_work',
                    args: { docname: frm.doc.name },
                    callback: function (r) {
                        if (r.message && r.message.status === 'success') {
                            frappe.show_alert({
                                message: r.message.message || __('Work started'),
                                indicator: 'green'
                            });
                            frm.reload_doc();
                        }
                    }
                });
            }, __('Actions')).addClass('btn-primary');
        }

        // Hold button - Scheduled, In Progress -> On Hold
        if (status === 'Scheduled' || status === 'In Progress') {
            frm.add_custom_button(__('Hold'), function () {
                frappe.prompt({
                    fieldtype: 'Small Text',
                    label: __('Reason for Hold'),
                    fieldname: 'reason',
                    reqd: 1
                }, function (values) {
                    frappe.call({
                        method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.hold_work',
                        args: {
                            docname: frm.doc.name,
                            reason: values.reason
                        },
                        callback: function (r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.show_alert({
                                    message: r.message.message || __('Work put on hold'),
                                    indicator: 'orange'
                                });
                                frm.reload_doc();
                            }
                        }
                    });
                }, __('Put on Hold'), __('Submit'));
            }, __('Actions')).addClass('btn-warning');
        }

        // Submit button - In Progress -> In Review
        if (status === 'In Progress') {
            frm.add_custom_button(__('Submit for Review'), function () {
                frappe.confirm(
                    __('Are you sure you want to submit this survey for review? You will not be able to edit after submission.'),
                    function () {
                        frappe.call({
                            method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.submit_survey',
                            args: { docname: frm.doc.name },
                            callback: function (r) {
                                if (r.message && r.message.status === 'success') {
                                    frappe.show_alert({
                                        message: r.message.message || __('Survey submitted'),
                                        indicator: 'green'
                                    });
                                    frm.reload_doc();
                                }
                            }
                        });
                    }
                );
            }, __('Actions')).addClass('btn-success');
        }
    }

    // MANAGER ACTIONS
    if (is_manager || is_admin) {
        // Approve button - In Review -> Approved
        if (status === 'In Review') {
            frm.add_custom_button(__('Approve'), function () {
                frappe.prompt({
                    fieldtype: 'Small Text',
                    label: __('Approval Comment'),
                    fieldname: 'comment',
                    reqd: 1
                }, function (values) {
                    frappe.call({
                        method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.approve_survey',
                        args: {
                            docname: frm.doc.name,
                            comment: values.comment
                        },
                        callback: function (r) {
                            if (r.message && r.message.status === 'success') {
                                // Show standard approval message
                                frappe.show_alert({
                                    message: r.message.message || __('Survey approved'),
                                    indicator: 'green'
                                });

                                // Show 30-second notification for quotation creation
                                if (r.message.quotation_created && r.message.quotation_name) {
                                    frappe.show_alert({
                                        message: __('Technical Survey approved. Quotation <b>{0}</b> created successfully for this lead. <a href="/app/quotation/{0}">Click to open</a>', [r.message.quotation_name]),
                                        indicator: 'blue'
                                    }, 30);  // 30-second duration
                                }

                                frm.reload_doc();
                            }
                        }
                    });
                }, __('Approve Survey'), __('Approve'));
            }, __('Actions')).addClass('btn-success');
        }

        // Close button - Any active status -> Closed
        if (status !== 'Closed' && status !== 'Approved') {
            frm.add_custom_button(__('Close'), function () {
                frappe.prompt({
                    fieldtype: 'Small Text',
                    label: __('Reason for Closing'),
                    fieldname: 'reason',
                    reqd: 1
                }, function (values) {
                    frappe.call({
                        method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.close_survey',
                        args: {
                            docname: frm.doc.name,
                            reason: values.reason
                        },
                        callback: function (r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.show_alert({
                                    message: r.message.message || __('Survey closed'),
                                    indicator: 'red'
                                });
                                frm.reload_doc();
                            }
                        }
                    });
                }, __('Close Survey'), __('Close'));
            }, __('Actions')).addClass('btn-danger');
        }

        // Reopen button - Closed, On Hold -> Reopened
        if (status === 'Closed' || status === 'On Hold') {
            frm.add_custom_button(__('Reopen'), function () {
                frappe.prompt({
                    fieldtype: 'Small Text',
                    label: __('Reason for Reopening'),
                    fieldname: 'reason',
                    reqd: 1
                }, function (values) {
                    frappe.call({
                        method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.reopen_survey',
                        args: {
                            docname: frm.doc.name,
                            reason: values.reason
                        },
                        callback: function (r) {
                            if (r.message && r.message.status === 'success') {
                                frappe.show_alert({
                                    message: r.message.message || __('Survey reopened'),
                                    indicator: 'blue'
                                });
                                frm.reload_doc();
                            }
                        }
                    });
                }, __('Reopen Survey'), __('Reopen'));
            }, __('Actions')).addClass('btn-primary');
        }
    }

    // SALES - View linked Quotation (auto-created on approval)
    const is_sales_manager = frappe.user.has_role('Sales Manager');
    if ((is_sales_manager || is_admin) && status === 'Approved') {
        // Check if quotation exists
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Quotation',
                filters: { custom_technical_survey: frm.doc.name },
                fieldname: 'name'
            },
            async: false,
            callback: function (r) {
                if (r.message && r.message.name) {
                    frm.add_custom_button(__('View Quotation'), function () {
                        frappe.set_route('Form', 'Quotation', r.message.name);
                    }, __('Links')).addClass('btn-primary');
                }
            }
        });
    }
}




// =============================================================================
// BOM FUNCTIONS
// =============================================================================

function setup_filters(frm) {
    // Filter dropdowns from STORED BOM data only

    frm.set_query('selected_panel', function () {
        return get_component_filter(frm, 'Panels');
    });

    frm.set_query('selected_inverter', function () {
        return get_component_filter(frm, 'Inverters');
    });

    frm.set_query('selected_battery', function () {
        return get_component_filter(frm, 'Battery');
    });

    // Validate current selections against BOM
    validate_component_selections(frm);
}

function get_component_filter(frm, item_group) {
    // Get item codes from stored BOM data by item_group
    let bom_items = frm.doc.bom_other_items || [];

    let matching_items = bom_items
        .filter(row => row.item_group === item_group)
        .map(row => row.item);

    if (matching_items.length > 0) {
        // Use query parameter to hide "Filters applied for" message
        return {
            query: 'solar_erp.solar_erp.api.technical_survey_bom.get_bom_items_for_dropdown',
            filters: {
                'allowed_items': matching_items,
                'item_group': item_group,
                is_sales_item: 1,
                disabled: 0

            }
        };
    }

    // Fallback to empty result if no BOM data
    return {
        filters: {
            'name': ['in', []]
        }
    };
}

function populate_bom_from_proposed_system(frm) {
    // For NEW documents, use get_bom_payload (doesn't require saved doc)
    // For SAVED documents, use populate_bom_items (server-side storage)

    if (frm.is_new()) {
        // Client-side population for new documents
        frappe.call({
            method: 'solar_erp.solar_erp.api.technical_survey_bom.get_bom_payload',
            args: {
                proposed_system_item_code: frm.doc.proposed_system
            },
            callback: function (r) {
                if (r.message && !r.message.error) {
                    populate_bom_fields_client_side(frm, r.message);
                    frappe.show_alert({
                        message: __('BOM populated. Save the document to persist changes.'),
                        indicator: 'blue'
                    }, 5);
                } else {
                    frappe.msgprint({
                        title: __('No BOM Found'),
                        message: r.message.error || __('No active BOM found for selected Proposed System.'),
                        indicator: 'red'
                    });
                }
            }
        });
    } else {
        // Server-side population for saved documents
        frappe.call({
            method: 'solar_erp.solar_erp.doctype.technical_survey.technical_survey.populate_bom_items',
            args: {
                docname: frm.doc.name,
                proposed_system_item_code: frm.doc.proposed_system
            },
            callback: function (r) {
                if (r.message && r.message.success) {
                    frm.reload_doc();
                    frappe.show_alert({
                        message: __('BOM populated from proposed system. Components auto-selected where possible.'),
                        indicator: 'green'
                    }, 5);
                } else if (r.exc) {
                    frappe.msgprint({
                        title: __('Error'),
                        message: r.exc || __('Failed to populate BOM items'),
                        indicator: 'red'
                    });
                }
            }
        });
    }
}

// Client-side BOM population for new documents
function populate_bom_fields_client_side(frm, payload) {
    // Set BOM reference
    frm.set_value('bom_reference', payload.bom);

    // Set quantities
    frm.set_value('panel_qty_from_bom', payload.qty_summary.panel_qty_from_bom || 0);
    frm.set_value('inverter_qty_from_bom', payload.qty_summary.inverter_qty_from_bom || 0);
    frm.set_value('battery_qty_from_bom', payload.qty_summary.battery_qty_from_bom || 0);

    // Auto-select components if only one option
    if (payload.default_selected_panel) {
        frm.set_value('selected_panel', payload.default_selected_panel);
    } else {
        frm.set_value('selected_panel', '');
    }

    if (payload.default_selected_inverter) {
        frm.set_value('selected_inverter', payload.default_selected_inverter);
    } else {
        frm.set_value('selected_inverter', '');
    }

    if (payload.default_selected_battery) {
        frm.set_value('selected_battery', payload.default_selected_battery);
    } else {
        frm.set_value('selected_battery', '');
    }

    // Clear and populate BOM items table using all_items (with correct item_group)
    frm.clear_table('bom_other_items');

    // DEBUG: Log what we received from API
    console.log('=== POPULATE BOM FIELDS ===');
    console.log('all_items count:', payload.all_items ? payload.all_items.length : 0);

    if (payload.all_items && payload.all_items.length > 0) {
        payload.all_items.forEach(function (item) {
            // Use add_child and set properties via Object.assign
            let row = frm.add_child('bom_other_items');
            Object.assign(row, {
                item: item.item_code,
                item_name: item.item_name,
                item_group: item.item_group,
                qty: item.qty,
                uom: item.uom,
                notes: item.description || ''
            });
        });
        console.log('Added', frm.doc.bom_other_items.length, 'items to child table');
    } else {
        console.log('WARNING: No all_items in payload or empty');
    }

    frm.refresh_field('bom_other_items');

    // Re-setup filters with new data
    console.log('Setting up filters with', frm.doc.bom_other_items.length, 'BOM items');
    setup_filters(frm);
}

function clear_bom_fields(frm) {
    frm.set_value('bom_reference', '');
    frm.set_value('selected_panel', '');
    frm.set_value('selected_inverter', '');
    frm.set_value('selected_battery', '');
    frm.set_value('panel_qty_from_bom', 0);
    frm.set_value('inverter_qty_from_bom', 0);
    frm.set_value('battery_qty_from_bom', 0);
    frm.clear_table('bom_other_items');
    frm.refresh_field('bom_other_items');
}


function validate_component_selections(frm) {
    // Validate that selected components exist in BOM
    // Clear invalid selections

    let bom_items = frm.doc.bom_other_items || [];

    // Get allowed items by group
    let allowed_panels = bom_items
        .filter(row => row.item_group === 'Panels')
        .map(row => row.item);

    let allowed_inverters = bom_items
        .filter(row => row.item_group === 'Inverters')
        .map(row => row.item);

    let allowed_batteries = bom_items
        .filter(row => row.item_group === 'Battery')
        .map(row => row.item);

    // Clear invalid panel selection
    if (frm.doc.selected_panel && allowed_panels.length > 0) {
        if (!allowed_panels.includes(frm.doc.selected_panel)) {
            frm.set_value('selected_panel', '');
            frappe.show_alert({
                message: __('Selected panel is not in BOM. Please re-select.'),
                indicator: 'orange'
            });
        }
    }

    // Clear invalid inverter selection
    if (frm.doc.selected_inverter && allowed_inverters.length > 0) {
        if (!allowed_inverters.includes(frm.doc.selected_inverter)) {
            frm.set_value('selected_inverter', '');
            frappe.show_alert({
                message: __('Selected inverter is not in BOM. Please re-select.'),
                indicator: 'orange'
            });
        }
    }

    // Clear invalid battery selection
    if (frm.doc.selected_battery && allowed_batteries.length > 0) {
        if (!allowed_batteries.includes(frm.doc.selected_battery)) {
            frm.set_value('selected_battery', '');
            frappe.show_alert({
                message: __('Selected battery is not in BOM. Please re-select.'),
                indicator: 'orange'
            });
        }
    }
}


// =============================================================================
// INITIATE TECHNICAL SURVEY BUTTON
// =============================================================================

function add_initiate_survey_button(frm) {
    /**
     * Add "Initiate Technical Survey" button for System Manager and Administrator
     * This button initiates the survey so vendor company can see it
     */

    console.log('=== Initiate Survey Button Debug ===');
    console.log('Status:', frm.doc.status);
    console.log('assigned_vendor:', frm.doc.assigned_vendor);
    console.log('lead:', frm.doc.lead);

    // Only show for saved documents
    if (frm.is_new()) {
        console.log('Button hidden: Document is new');
        return;
    }

    // Check if user has required roles
    const is_system_manager = frappe.user.has_role('System Manager');
    const is_administrator = frappe.user.has_role('Administrator');

    console.log('is_system_manager:', is_system_manager);
    console.log('is_administrator:', is_administrator);

    if (!is_system_manager && !is_administrator) {
        console.log('Button hidden: User does not have System Manager or Administrator role');
        return;
    }

    // Only show if vendor is assigned (from Initiate Job)
    if (!frm.doc.assigned_vendor) {
        console.log('Button hidden: No assigned_vendor');
        return;
    }

    // Only show if status is Draft (not yet initiated)
    if (frm.doc.status !== 'Draft') {
        console.log('Button hidden: Status is not Draft, current status:', frm.doc.status);
        return;
    }

    console.log('✅ All conditions met - Adding button');

    // Add the button
    frm.add_custom_button(__('Initiate Technical Survey'), function () {
        frappe.confirm(
            __('This will initiate the Technical Survey and make it visible to vendor company <b>{0}</b>. The status will change to "Scheduled". Continue?', [frm.doc.assigned_vendor]),
            function () {
                // Call server-side method
                frappe.call({
                    method: 'solar_erp.solar_erp.api.lead_vendor.initiate_survey_for_vendor',
                    args: {
                        survey_name: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __('Initiating Technical Survey...'),
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.show_alert({
                                message: __('Technical Survey initiated for {0}', [r.message.vendor_company]),
                                indicator: 'green'
                            }, 5);
                            frm.reload_doc();
                        } else if (r.message && r.message.error) {
                            frappe.msgprint({
                                title: __('Error'),
                                message: r.message.error,
                                indicator: 'red'
                            });
                        }
                    },
                    error: function (r) {
                        frappe.msgprint({
                            title: __('Error'),
                            message: __('Failed to initiate survey. Please try again.'),
                            indicator: 'red'
                        });
                    }
                });
            }
        );
    }, __('Actions')).addClass('btn-primary');
}

