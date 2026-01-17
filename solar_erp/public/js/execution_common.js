// execution_common.js (REFINED)
// Single responsibility: UI helpers for Workflow-based execution doctypes
// NO business state mutation. NO status hacking.

frappe.provide('solar_erp.execution');

/* ------------------------------------------------------------
 * ROLE HELPERS
 * ------------------------------------------------------------ */
solar_erp.execution.has_any_role = function (roles) {
    return roles.some(role => frappe.user.has_role(role));
};

solar_erp.execution.is_vendor_exec = function (doctype) {
    const role_map = {
        'Technical Survey': 'Technical Survey Executive',
        'Structure Mounting': 'Structure Mounting Executive',
        'Panel Installation': 'Panel Installation Executive',
        'Meter Installation': 'Meter Installation Executive',
        'Meter Commissioning': 'Meter Commissioning Executive',
        'Verification Handover': 'Verification Handover Executive'
    };

    return solar_erp.execution.has_any_role([
        'Vendor Executive',
        role_map[doctype],
        'System Manager',
        'Administrator'
    ].filter(Boolean));
};

solar_erp.execution.is_project_manager = function (doctype) {
    const role_map = {
        'Technical Survey': 'Technical Survey Manager',
        'Structure Mounting': 'Structure Mounting Manager',
        'Panel Installation': 'Panel Installation Manager',
        'Meter Installation': 'Meter Installation Manager',
        'Meter Commissioning': 'Meter Commissioning Manager',
        'Verification Handover': 'Verification Handover Manager'
    };

    return solar_erp.execution.has_any_role([
        'Project Manager',
        role_map[doctype],
        'System Manager',
        'Administrator'
    ].filter(Boolean));
};

/* ------------------------------------------------------------
 * WORKFLOW UI
 * ------------------------------------------------------------ */
solar_erp.execution.WORKFLOW_COLORS = {
    'Draft': 'grey',
    'Assigned to Vendor': 'blue',
    'In Progress': 'orange',
    'On Hold': 'yellow',
    'Submitted': 'purple',
    'Approved': 'green',
    'Closed': 'red'
};

solar_erp.execution.set_workflow_indicator = function (frm) {
    if (!frm.doc.workflow_state) return;

    const color = solar_erp.execution.WORKFLOW_COLORS[frm.doc.workflow_state] || 'grey';
    frm.page.set_indicator(frm.doc.workflow_state, color);
};

/* ------------------------------------------------------------
 * DASHBOARD HELPERS
 * ------------------------------------------------------------ */
solar_erp.execution.show_advance_payment_status = function (frm) {
    if (!frm.doc.job_file || frm.doctype === 'Technical Survey') return;

    frappe.call({
        method: 'solar_erp.solar_erp.api.execution_workflow.check_advance_payment_gate',
        args: { job_file: frm.doc.job_file },
        callback: function (r) {
            if (!r.message) return;

            if (!r.message.verified && !r.message.bypass) {
                frm.dashboard.add_comment(
                    __('⚠️ Advance Payment not verified. Execution blocked.'),
                    'yellow',
                    true
                );
            }

            if (r.message.verified) {
                frm.dashboard.add_comment(
                    __('✅ Advance Payment verified'),
                    'green',
                    true
                );
            }
        }
    });
};

/* ------------------------------------------------------------
 * NAVIGATION (NEXT STAGE)
 * ------------------------------------------------------------ */
solar_erp.execution.NEXT_STAGE_MAP = {
    'Technical Survey': {
        field: 'linked_structure_mounting',
        doctype: 'Structure Mounting',
        label: 'Go to Structure Mounting'
    },
    'Structure Mounting': {
        field: 'linked_panel_installation',
        doctype: 'Panel Installation',
        label: 'Go to Panel Installation'
    },
    'Panel Installation': {
        field: 'linked_meter_installation',
        doctype: 'Meter Installation',
        label: 'Go to Meter Installation'
    },
    'Meter Installation': {
        field: 'linked_meter_commissioning',
        doctype: 'Meter Commissioning',
        label: 'Go to Meter Commissioning'
    },
    'Meter Commissioning': {
        field: 'linked_verification_handover',
        doctype: 'Verification Handover',
        label: 'Go to Verification Handover'
    }
};

solar_erp.execution.add_next_stage_button = function (frm) {
    const config = solar_erp.execution.NEXT_STAGE_MAP[frm.doctype];
    if (!config) return;

    if (frm.doc.workflow_state !== 'Approved') return;

    const linked = frm.doc[config.field];
    if (!linked) return;

    frm.add_custom_button(__(config.label), function () {
        frappe.set_route('Form', config.doctype, linked);
    }, __('Links')).addClass('btn-primary');
};

/* ------------------------------------------------------------
 * MAIN ENTRY (called from each doctype JS)
 * ------------------------------------------------------------ */
solar_erp.execution.apply = function (frm) {
    if (frm.is_new()) return;

    solar_erp.execution.set_workflow_indicator(frm);
    solar_erp.execution.show_advance_payment_status(frm);
    solar_erp.execution.add_next_stage_button(frm);
};
