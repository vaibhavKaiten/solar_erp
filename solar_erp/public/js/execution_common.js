// Copyright (c) 2025, KaitenSoftware
// Shared Execution Controller for Action Buttons
// Provides consistent UI behavior across all execution doctypes

frappe.provide('solar_erp.execution');

/**
 * Role detection helpers
 */
solar_erp.execution.is_vendor_executive = function (doctype) {
    // Check generic Vendor Executive role
    if (frappe.user.has_role('Vendor Executive') ||
        frappe.user.has_role('System Manager') ||
        frappe.user.has_role('Administrator')) {
        return true;
    }

    // Check doctype-specific executive roles
    const executive_role_map = {
        'Technical Survey': 'Technical Survey Executive',
        'Structure Mounting': 'Structure Mounting Executive',
        'Panel Installation': 'Panel Installation Executive',
        'Meter Installation': 'Meter Installation Executive',
        'Meter Commissioning': 'Meter Commissioning Executive',
        'Verification Handover': 'Verification Handover Executive'
    };

    const specific_role = executive_role_map[doctype];
    if (specific_role && frappe.user.has_role(specific_role)) {
        return true;
    }

    return false;
};

solar_erp.execution.is_project_manager = function (doctype) {
    // Check generic Project Manager role
    if (frappe.user.has_role('Project Manager') ||
        frappe.user.has_role('System Manager') ||
        frappe.user.has_role('Administrator')) {
        return true;
    }

    // Check doctype-specific manager roles
    const manager_role_map = {
        'Technical Survey': 'Technical Survey Manager',
        'Structure Mounting': 'Structure Mounting Manager',
        'Panel Installation': 'Panel Installation Manager',
        'Meter Installation': 'Meter Installation Manager',
        'Meter Commissioning': 'Meter Commissioning Manager',
        'Verification Handover': 'Verification Handover Manager'
    };

    const specific_role = manager_role_map[doctype];
    if (specific_role && frappe.user.has_role(specific_role)) {
        return true;
    }

    return false;
};

solar_erp.execution.is_admin = function () {
    return frappe.user.has_role('System Manager') ||
        frappe.user.has_role('Administrator');
};

/**
 * Status color mapping
 */
solar_erp.execution.STATUS_COLORS = {
    'Draft': 'grey',
    'Scheduled': 'blue',
    'In Progress': 'orange',
    'On Hold': 'yellow',
    'In Review': 'purple',
    'Submitted': 'purple',
    'Ready for Review': 'purple',
    'Reopened': 'cyan',
    'Rework': 'red',
    'Rejected': 'red',
    'Closed': 'red',
    'Approved': 'green'
};

/**
 * Set page indicator based on status
 */
solar_erp.execution.set_status_indicator = function (frm) {
    const color = solar_erp.execution.STATUS_COLORS[frm.doc.status] || 'grey';
    frm.page.set_indicator(frm.doc.status, color);
};

/**
 * Add all action buttons based on role and status
 */
solar_erp.execution.add_action_buttons = function (frm) {
    if (frm.is_new()) return;

    // Clear existing custom buttons
    frm.clear_custom_buttons();

    const status = frm.doc.status;
    const is_vendor = solar_erp.execution.is_vendor_executive(frm.doctype);
    const is_pm = solar_erp.execution.is_project_manager(frm.doctype);
    const is_admin = solar_erp.execution.is_admin();

    // =========================================================================
    // SPECIFIC DOCTYPE ACTIONS
    // =========================================================================


    // =========================================================================
    if (is_vendor || is_admin) {
        // Start button - Draft, Scheduled, Reopened, Rework -> In Progress
        // Exception: Structure Mounting cannot be started from Draft (must be Initiated first)
        let allowed_start_statuses = ['Draft', 'Scheduled', 'Reopened', 'Rework'];

        if (frm.doctype === 'Structure Mounting') {
            // Structure Mounting start flow: Assigned to Vendor -> In Progress
            // So it should show for 'Assigned to Vendor', 'Scheduled', 'Reopened', 'Rework'
            // It must NOT show for 'Draft'
            allowed_start_statuses = ['Assigned to Vendor', 'Scheduled', 'Reopened', 'Rework'];
        }

        if (allowed_start_statuses.includes(status)) {
            frm.add_custom_button(__('Start'), function () {
                solar_erp.execution.start_work(frm);
            }, __('Actions')).addClass('btn-primary');
        }

        // Hold button - Scheduled, In Progress -> On Hold
        if (['Scheduled', 'In Progress'].includes(status)) {
            frm.add_custom_button(__('Hold'), function () {
                solar_erp.execution.hold_work(frm);
            }, __('Actions')).addClass('btn-warning');
        }

        // Submit button - In Progress -> Ready for Review
        if (status === 'In Progress') {
            frm.add_custom_button(__('Submit for Review'), function () {
                solar_erp.execution.submit_for_review(frm);
            }, __('Actions')).addClass('btn-success');
        }
    }

    // =========================================================================
    // PROJECT MANAGER ACTIONS
    // =========================================================================
    if (is_pm || is_admin) {
        // Approve button - In Review OR Submitted OR Ready for Review -> Approved
        // Technical Survey uses "In Review", Structure Mounting uses "Submitted", others use "Ready for Review"
        if (status === 'In Review' || status === 'Submitted' || status === 'Ready for Review') {
            frm.add_custom_button(__('Approve'), function () {
                solar_erp.execution.approve(frm);
            }, __('Actions')).addClass('btn-success');

            // Rework button
            frm.add_custom_button(__('Request Rework'), function () {
                solar_erp.execution.request_rework(frm);
            }, __('Actions')).addClass('btn-warning');
        }

        // Reopen button - Closed, On Hold -> Reopened
        if (['Closed', 'On Hold'].includes(status)) {
            frm.add_custom_button(__('Reopen'), function () {
                solar_erp.execution.reopen_stage(frm);
            }, __('Actions')).addClass('btn-primary');
        }

        // Close button - Any active status except Approved -> Closed
        if (!['Closed', 'Approved'].includes(status)) {
            frm.add_custom_button(__('Close'), function () {
                solar_erp.execution.close_stage(frm);
            }, __('Actions')).addClass('btn-danger');
        }
    }

    // =========================================================================
    // NAVIGATION TO NEXT STAGE
    // =========================================================================
    if (status === 'Approved') {
        solar_erp.execution.add_next_stage_button(frm);
    }
};

/**
 * Add button to navigate to next stage
 */
solar_erp.execution.add_next_stage_button = function (frm) {
    const next_stage_map = {
        'Technical Survey': { field: 'linked_structure_mounting', doctype: 'Structure Mounting', label: 'Go to Structure Mounting' },
        'Structure Mounting': { field: 'linked_panel_installation', doctype: 'Panel Installation', label: 'Go to Panel Installation' },
        'Panel Installation': { field: 'linked_meter_installation', doctype: 'Meter Installation', label: 'Go to Meter Installation' },
        'Meter Installation': { field: 'linked_meter_commissioning', doctype: 'Meter Commissioning', label: 'Go to Meter Commissioning' },
        'Meter Commissioning': { field: 'linked_verification_handover', doctype: 'Verification Handover', label: 'Go to Verification Handover' }
    };

    const stage_info = next_stage_map[frm.doctype];
    if (!stage_info) return;

    const linked_doc = frm.doc[stage_info.field];
    if (linked_doc) {
        frm.add_custom_button(__(stage_info.label), function () {
            frappe.set_route('Form', stage_info.doctype, linked_doc);
        }, __('Links')).addClass('btn-primary');
    }
};

/**
 * Vendor Executive: Start Work
 */
solar_erp.execution.start_work = function (frm) {
    frappe.call({
        method: 'solar_erp.solar_erp.api.execution_actions.start_work',
        args: {
            doctype: frm.doctype,
            docname: frm.doc.name
        },
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
};

/**
 * Vendor Executive: Hold Work (reason mandatory)
 */
solar_erp.execution.hold_work = function (frm) {
    frappe.prompt({
        fieldtype: 'Small Text',
        label: __('Reason for Hold'),
        fieldname: 'reason',
        reqd: 1
    }, function (values) {
        frappe.call({
            method: 'solar_erp.solar_erp.api.execution_actions.hold_work',
            args: {
                doctype: frm.doctype,
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
};

/**
 * Vendor Executive: Submit for Review
 */
solar_erp.execution.submit_for_review = function (frm) {
    frappe.confirm(
        __('Are you sure you want to submit for review?'),
        function () {
            frappe.call({
                method: 'solar_erp.solar_erp.api.execution_actions.submit_for_review',
                args: {
                    doctype: frm.doctype,
                    docname: frm.doc.name
                },
                callback: function (r) {
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: r.message.message || __('Submitted for review'),
                            indicator: 'green'
                        });
                        frm.reload_doc();
                    }
                }
            });
        }
    );
};

/**
 * Project Manager: Approve (comment mandatory)
 */
solar_erp.execution.approve = function (frm) {
    frappe.prompt({
        fieldtype: 'Small Text',
        label: __('Approval Comment'),
        fieldname: 'comment',
        reqd: 1
    }, function (values) {
        frappe.call({
            method: 'solar_erp.solar_erp.api.execution_actions.approve',
            args: {
                doctype: frm.doctype,
                docname: frm.doc.name,
                comment: values.comment
            },
            callback: function (r) {
                if (r.message && r.message.status === 'success') {
                    frappe.show_alert({
                        message: r.message.message || __('Approved'),
                        indicator: 'green'
                    });

                    // Show next stage notification if created
                    if (r.message.next_stage_created) {
                        frappe.show_alert({
                            message: __('Next stage created: {0}', [r.message.next_stage_created]),
                            indicator: 'blue'
                        }, 10);
                    }

                    frm.reload_doc();
                }
            }
        });
    }, __('Approve'), __('Approve'));
};

/**
 * Project Manager: Request Rework (comment mandatory)
 */
solar_erp.execution.request_rework = function (frm) {
    frappe.prompt({
        fieldtype: 'Small Text',
        label: __('Rework Reason'),
        fieldname: 'comment',
        reqd: 1
    }, function (values) {
        frappe.call({
            method: 'solar_erp.solar_erp.api.execution_actions.request_rework',
            args: {
                doctype: frm.doctype,
                docname: frm.doc.name,
                comment: values.comment
            },
            callback: function (r) {
                if (r.message && r.message.status === 'success') {
                    frappe.show_alert({
                        message: r.message.message || __('Rework requested'),
                        indicator: 'orange'
                    });
                    frm.reload_doc();
                }
            }
        });
    }, __('Request Rework'), __('Submit'));
};

/**
 * Project Manager: Close Stage (comment mandatory)
 */
solar_erp.execution.close_stage = function (frm) {
    frappe.prompt({
        fieldtype: 'Small Text',
        label: __('Reason for Closing'),
        fieldname: 'comment',
        reqd: 1
    }, function (values) {
        frappe.call({
            method: 'solar_erp.solar_erp.api.execution_actions.close_stage',
            args: {
                doctype: frm.doctype,
                docname: frm.doc.name,
                comment: values.comment
            },
            callback: function (r) {
                if (r.message && r.message.status === 'success') {
                    frappe.show_alert({
                        message: r.message.message || __('Closed'),
                        indicator: 'red'
                    });
                    frm.reload_doc();
                }
            }
        });
    }, __('Close'), __('Close'));
};

/**
 * Project Manager: Reopen Stage (comment mandatory)
 */
solar_erp.execution.reopen_stage = function (frm) {
    frappe.prompt({
        fieldtype: 'Small Text',
        label: __('Reason for Reopening'),
        fieldname: 'comment',
        reqd: 1
    }, function (values) {
        frappe.call({
            method: 'solar_erp.solar_erp.api.execution_actions.reopen_stage',
            args: {
                doctype: frm.doctype,
                docname: frm.doc.name,
                comment: values.comment
            },
            callback: function (r) {
                if (r.message && r.message.status === 'success') {
                    frappe.show_alert({
                        message: r.message.message || __('Reopened'),
                        indicator: 'blue'
                    });
                    frm.reload_doc();
                }
            }
        });
    }, __('Reopen'), __('Reopen'));
};

/**
 * Check if advance payment is verified for the job
 */
solar_erp.execution.check_advance_payment = function (job_file, callback) {
    frappe.call({
        method: 'solar_erp.solar_erp.api.execution_workflow.check_advance_payment_gate',
        args: {
            job_file: job_file
        },
        callback: function (r) {
            if (callback) {
                callback(r.message);
            }
        }
    });
};

/**
 * Show advance payment status banner
 */
solar_erp.execution.show_payment_status = function (frm) {
    if (!frm.doc.job_file) return;

    // Only show for stages after Technical Survey
    if (frm.doctype === 'Technical Survey') return;

    solar_erp.execution.check_advance_payment(frm.doc.job_file, function (result) {
        if (result && !result.verified && !result.bypass) {
            frm.dashboard.add_comment(
                __('⚠️ Advance Payment not verified. Physical execution is blocked until payment is received.'),
                'yellow',
                true
            );
        } else if (result && result.verified) {
            frm.dashboard.add_comment(
                __('✅ Advance Payment verified'),
                'green',
                true
            );
        }
    });
};
