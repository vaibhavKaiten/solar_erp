/**
 * Material Request Client Script - GST Rate Splitting
 * Adds "Split by GST Rate" button for manual Material Requests
 */

frappe.ui.form.on('Material Request', {
    refresh: function (frm) {
        // Add "Split by GST Rate" button if conditions are met
        // Allow for Draft (0) or Submitted (1) with Pending/Ordered status
        // BUT NOT if already consolidated (consolidated MRs should not be split)
        if ((frm.doc.docstatus === 0 ||
            (frm.doc.docstatus === 1 && ['Pending', 'Ordered'].includes(frm.doc.status))) &&
            !frm.doc.custom_is_split && // Not already split
            !frm.doc.custom_consolidated && // Not consolidated
            frm.doc.items && frm.doc.items.length > 0) { // Has items

            frm.add_custom_button(__('Split by GST Rate'), function () {
                split_mr_by_gst_rate(frm);
            }, __('Actions'));
        }

        // Add "Mark as Consolidated" button for procurement planning
        // Only show if: Submitted (docstatus=1) AND not yet consolidated
        if (frm.doc.docstatus === 1 && !frm.doc.custom_consolidated) {
            frm.add_custom_button(__('Mark as Consolidated'), function () {
                mark_as_consolidated(frm);
            }, __('Actions'));
        }

        // Show warning if MR contains mixed GST items
        // BUT NOT if already consolidated (no need to warn about consolidated MRs)
        if (frm.doc.items && frm.doc.items.length > 1 &&
            !frm.doc.custom_is_split &&
            !frm.doc.custom_consolidated) {
            check_mixed_gst_warning(frm);
        }
    },

    before_submit: function (frm) {
        // Prevent submission if marked as split
        if (frm.doc.custom_is_split) {
            frappe.msgprint({
                title: __('Cannot Submit'),
                message: __('This Material Request has been split. Please submit the individual split requests instead.'),
                indicator: 'red'
            });
            frappe.validated = false;
        }
    }
});

/**
 * Check if MR has mixed GST items and show warning
 */
async function check_mixed_gst_warning(frm) {
    // Fetch GST rates for all items
    const gst_rates = new Set();

    for (const item_row of frm.doc.items) {
        const gst_rate = await get_item_gst_rate(item_row.item_code);
        gst_rates.add(gst_rate);
    }

    if (gst_rates.size > 1) {
        frm.dashboard.add_comment(
            __('Warning: This Material Request contains items with different GST rates ({0}). Consider using "Split by GST Rate" for better compliance.',
                [Array.from(gst_rates).join('%, ') + '%']),
            'yellow',
            true
        );
    }
}

/**
 * Main function to split Material Request by GST rate
 */
async function split_mr_by_gst_rate(frm) {
    frappe.confirm(
        __('This will create separate Material Requests for each GST rate group and cancel this MR. Continue?'),
        async function () {
            frappe.dom.freeze(__('Splitting Material Request by GST rate...'));

            try {
                // Step 1: Fetch GST rates for all items
                console.log('Step 1: Fetching GST rates for items...');
                const items_with_gst = await fetch_items_with_gst(frm);
                console.log('Items with GST:', items_with_gst);

                // Step 2: Group items by GST rate
                console.log('Step 2: Grouping by GST rate...');
                const gst_groups = group_items_by_gst(items_with_gst);
                console.log('GST Groups:', gst_groups);

                // Validation: Check if split is needed
                if (Object.keys(gst_groups).length === 1) {
                    frappe.msgprint(__('All items have the same GST rate. No split needed.'));
                    frappe.dom.unfreeze();
                    return;
                }

                // CRITICAL: Store original MR data before cancelling
                console.log('Step 3: Storing original MR data...');
                const original_mr_name = frm.doc.name;
                const mr_data = {
                    material_request_type: frm.doc.material_request_type,
                    transaction_date: frm.doc.transaction_date,
                    schedule_date: frm.doc.schedule_date,
                    company: frm.doc.company,
                    set_warehouse: frm.doc.set_warehouse,
                    custom_sales_order: frm.doc.custom_sales_order
                };
                console.log('MR Data:', mr_data);

                // Step 4: Cancel/Delete original MR FIRST (to clear duplicate validation)
                console.log('Step 4: Cancelling original MR...');
                await cancel_original_mr(frm);
                console.log('Original MR cancelled successfully');

                // Step 5: Create new MRs for each GST group
                console.log('Step 5: Creating split MRs...');
                const new_mrs = await create_split_mrs_standalone(gst_groups, mr_data, original_mr_name);
                console.log('Created MRs:', new_mrs);

                if (new_mrs.length === 0) {
                    frappe.msgprint({
                        title: __('Warning'),
                        message: __('No Material Requests were created. Check console for details.'),
                        indicator: 'orange'
                    });
                    frappe.dom.unfreeze();
                    return;
                }

                // Show success message
                frappe.msgprint({
                    title: __('Split Complete'),
                    message: __('Created {0} Material Request(s):<br>{1}', [
                        new_mrs.length,
                        new_mrs.map(mr => `<a href="/app/material-request/${mr}">${mr}</a>`).join('<br>')
                    ]),
                    indicator: 'green'
                });

                // Navigate to MR list (original is already cancelled/deleted)
                setTimeout(function () {
                    frappe.set_route('List', 'Material Request');
                }, 1500);

            } catch (error) {
                console.error('Split Error Details:', error);
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to split Material Request: {0}', [error.message || error]),
                    indicator: 'red'
                });
            } finally {
                frappe.dom.unfreeze();
            }
        }
    );
}

/**
 * Fetch GST rate for a single item
 */
async function get_item_gst_rate(item_code) {
    try {
        // Method 1: Try to get from Item Tax Template via frappe.call (safer)
        const result = await frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Item',
                filters: { name: item_code },
                fieldname: ['name', 'item_name', 'gst_hsn_code']
            }
        });

        // Method 2: If Item has taxes table, fetch it
        const taxes_result = await frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Item',
                name: item_code
            }
        });

        if (taxes_result.message && taxes_result.message.taxes) {
            // Item has taxes configured
            for (const tax_row of taxes_result.message.taxes) {
                if (tax_row.item_tax_template) {
                    const template_name = tax_row.item_tax_template;

                    // Parse GST rate from template name
                    if (template_name.includes('5%') || template_name.includes('GST 5')) {
                        return 5;
                    } else if (template_name.includes('12%') || template_name.includes('GST 12')) {
                        return 12;
                    } else if (template_name.includes('18%') || template_name.includes('GST 18')) {
                        return 18;
                    } else if (template_name.includes('28%') || template_name.includes('GST 28')) {
                        return 28;
                    }
                }
            }
        }

        // Method 3: Fallback - check HSN code pattern
        if (result.message && result.message.gst_hsn_code) {
            const hsn = result.message.gst_hsn_code;
            // Common HSN patterns (you can customize this)
            if (hsn.startsWith('8541') || hsn.startsWith('8504')) {
                return 5; // Solar panels/inverters typically 5%
            }
        }

        // Default rate if cannot determine
        return 18;

    } catch (error) {
        console.error('Error fetching GST rate for', item_code, error);
        // Return default rate instead of failing
        return 18;
    }
}

/**
 * Fetch all items with their GST rates
 */
async function fetch_items_with_gst(frm) {
    const items_with_gst = [];

    for (const item_row of frm.doc.items) {
        const gst_rate = await get_item_gst_rate(item_row.item_code);

        items_with_gst.push({
            ...item_row,
            gst_rate: gst_rate
        });
    }

    return items_with_gst;
}

/**
 * Group items by GST rate
 */
function group_items_by_gst(items) {
    const groups = {};

    items.forEach(item => {
        const rate = item.gst_rate || 0;
        if (!groups[rate]) {
            groups[rate] = [];
        }
        groups[rate].push(item);
    });

    return groups;
}

/**
 * Create new Material Requests for each GST group
 */
async function create_split_mrs(gst_groups, frm) {
    const created_mrs = [];

    for (const [gst_rate, items] of Object.entries(gst_groups)) {
        // Prepare new MR document
        const new_mr = {
            doctype: 'Material Request',
            material_request_type: frm.doc.material_request_type,
            transaction_date: frm.doc.transaction_date,
            schedule_date: frm.doc.schedule_date,
            company: frm.doc.company,
            set_warehouse: frm.doc.set_warehouse,
            custom_gst_rate: parseFloat(gst_rate),
            custom_split_from: frm.doc.name,
            items: items.map(item => ({
                item_code: item.item_code,
                item_name: item.item_name,
                qty: item.qty,
                uom: item.uom,
                schedule_date: item.schedule_date,
                warehouse: item.warehouse,
                project: item.project,
                cost_center: item.cost_center
            })),
            custom_remarks: `Split from MR ${frm.doc.name} | GST Group: ${gst_rate}%`
        };

        // Create the MR
        const result = await frappe.call({
            method: 'frappe.client.insert',
            args: {
                doc: new_mr
            }
        });

        if (result.message) {
            created_mrs.push(result.message.name);

            frappe.show_alert({
                message: __('Created {0} for GST {1}%', [result.message.name, gst_rate]),
                indicator: 'green'
            }, 3);
        }
    }

    return created_mrs;
}

/**
 * Cancel the original MR (called BEFORE creating splits to avoid duplicate validation)
 * ALWAYS cancels (never deletes) so the document exists for custom_split_from link
 */
async function cancel_original_mr(frm) {
    try {
        // Check if MR is already submitted
        if (frm.doc.docstatus === 1) {
            // Already submitted - just cancel it
            await frappe.call({
                method: 'frappe.client.cancel',
                args: {
                    doctype: 'Material Request',
                    name: frm.doc.name
                }
            });

            frappe.show_alert({
                message: __('Original Material Request cancelled'),
                indicator: 'blue'
            }, 2);

        } else {
            // MR is in Draft - Submit then Cancel (so it still exists)
            // First mark as split to prevent workflow issues
            frm.set_value('custom_is_split', 1);
            frm.set_value('custom_remarks', `⚠️ OBSOLETE - Split into separate GST-based MRs. DO NOT USE.`);
            await frm.save();

            // Submit it
            await frappe.call({
                method: 'frappe.client.submit',
                args: {
                    doc: frm.doc
                }
            });

            // Now cancel it (document still exists with docstatus=2)
            await frappe.call({
                method: 'frappe.client.cancel',
                args: {
                    doctype: 'Material Request',
                    name: frm.doc.name
                }
            });

            frappe.show_alert({
                message: __('Original Material Request cancelled'),
                indicator: 'blue'
            }, 2);
        }
    } catch (error) {
        console.error('Could not cancel original MR:', error);
        throw new Error(`Failed to cancel original MR: ${error.message}`);
    }
}

/**
 * Create split MRs using stored data (not form context)
 */
async function create_split_mrs_standalone(gst_groups, mr_data, original_mr_name) {
    const created_mrs = [];

    console.log('create_split_mrs_standalone called with:', { gst_groups, mr_data, original_mr_name });

    for (const [gst_rate, items] of Object.entries(gst_groups)) {
        console.log(`Creating MR for GST ${gst_rate}%...`);

        // Prepare new MR document
        const new_mr = {
            doctype: 'Material Request',
            material_request_type: mr_data.material_request_type,
            transaction_date: mr_data.transaction_date,
            schedule_date: mr_data.schedule_date,
            company: mr_data.company,
            set_warehouse: mr_data.set_warehouse,
            custom_gst_rate: parseFloat(gst_rate),
            // Don't set custom_split_from - can't link to cancelled docs
            custom_sales_order: mr_data.custom_sales_order, // Preserve SO link
            items: items.map(item => ({
                item_code: item.item_code,
                item_name: item.item_name,
                qty: item.qty,
                uom: item.uom,
                schedule_date: item.schedule_date,
                warehouse: item.warehouse,
                project: item.project,
                cost_center: item.cost_center
            })),
            custom_remarks: `✂️ Split from MR ${original_mr_name} (cancelled) | GST Group: ${gst_rate}%`
        };

        console.log('MR Document to create:', new_mr);

        try {
            // Create the MR
            const result = await frappe.call({
                method: 'frappe.client.insert',
                args: {
                    doc: new_mr
                }
            });

            console.log('Creation result:', result);

            if (result.message) {
                created_mrs.push(result.message.name);

                frappe.show_alert({
                    message: __('Created {0} for GST {1}%', [result.message.name, gst_rate]),
                    indicator: 'green'
                }, 3);
            } else {
                console.error('No message in result:', result);
            }
        } catch (error) {
            console.error(`Error creating MR for GST ${gst_rate}%:`, error);
            frappe.msgprint({
                title: __('Error'),
                message: __('Failed to create MR for GST {0}%: {1}', [gst_rate, error.message || error]),
                indicator: 'red'
            });
        }
    }

    console.log('Total created MRs:', created_mrs);
    return created_mrs;
}

/**
 * Mark original MR as split and cancel/delete it
 */
async function mark_as_split(frm) {
    try {
        // Check if MR is already submitted
        if (frm.doc.docstatus === 1) {
            // Already submitted - just cancel it
            await frappe.call({
                method: 'frappe.client.cancel',
                args: {
                    doctype: 'Material Request',
                    name: frm.doc.name
                }
            });

            frappe.show_alert({
                message: __('Original Material Request cancelled successfully'),
                indicator: 'green'
            }, 3);

            // Navigate away
            setTimeout(function () {
                frappe.set_route('List', 'Material Request');
            }, 1000);

            return;
        }

        // MR is in Draft - try to delete it
        await frappe.call({
            method: 'frappe.client.delete',
            args: {
                doctype: 'Material Request',
                name: frm.doc.name
            }
        });

        frappe.show_alert({
            message: __('Original Material Request deleted successfully'),
            indicator: 'green'
        }, 3);

        // Navigate away from the deleted document  
        setTimeout(function () {
            frappe.set_route('List', 'Material Request');
        }, 1000);

    } catch (delete_error) {
        console.log('Deletion failed, trying to cancel instead:', delete_error);

        try {
            // Option 2: Submit then Cancel (changes status to "Cancelled")
            // First, mark as split to prevent workflow issues
            frm.set_value('custom_is_split', 1);
            frm.set_value('custom_remarks', `⚠️ OBSOLETE - Split into separate GST-based Material Requests. DO NOT USE THIS MR.`);

            // Submit the document (if not already submitted)
            await frm.save();
            if (frm.doc.docstatus === 0) {
                await frappe.call({
                    method: 'frappe.client.submit',
                    args: {
                        doc: frm.doc
                    }
                });
            }

            // Now cancel it (this will change status to "Cancelled")
            await frappe.call({
                method: 'frappe.client.cancel',
                args: {
                    doctype: 'Material Request',
                    name: frm.doc.name
                }
            });

            frappe.show_alert({
                message: __('Original Material Request cancelled successfully'),
                indicator: 'green'
            }, 3);

            // Navigate away
            setTimeout(function () {
                frappe.set_route('List', 'Material Request');
            }, 1000);

        } catch (cancel_error) {
            console.log('Could not cancel MR, marking as split:', cancel_error);

            // Option 3: Just mark as split (last resort)
            frm.set_value('custom_is_split', 1);
            frm.set_value('custom_remarks', `⚠️ OBSOLETE - Split into separate GST-based Material Requests. DO NOT USE THIS MR.`);

            await frm.save();

            frappe.msgprint({
                title: __('Original MR Marked as Obsolete'),
                message: __('This Material Request has been marked as obsolete. Status could not be changed to Cancelled due to permissions. Please manually cancel or delete this MR.'),
                indicator: 'orange'
            });
        }
    }
}

/**
 * Mark Material Request as Consolidated for Procurement Planning
 * This is a simple flag to indicate the MR has been considered for planning
 */
async function mark_as_consolidated(frm) {
    frappe.confirm(
        __('Mark this Material Request as consolidated for procurement planning?<br><br>This indicates the MR has been considered by the planning layer.'),
        async function () {
            try {
                // Set the consolidated flag
                frm.set_value('custom_consolidated', 1);
                await frm.save();

                frappe.show_alert({
                    message: __('Material Request marked as Consolidated'),
                    indicator: 'green'
                }, 3);

                // Clear any dashboard warnings
                frm.dashboard.clear_comment();

                // Force a full refresh to update button visibility and warnings
                setTimeout(() => {
                    frm.reload_doc();
                }, 500);

            } catch (error) {
                frappe.msgprint({
                    title: __('Error'),
                    message: __('Failed to mark as consolidated: {0}', [error.message || error]),
                    indicator: 'red'
                });
            }
        }
    );
}


