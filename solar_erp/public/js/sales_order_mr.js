/**
 * Sales Order Client Script - Auto Material Request Creation by GST Rate
 * Triggers on Sales Order submission to create GST-segregated Material Requests
 */

frappe.ui.form.on('Sales Order', {
    on_submit: function (frm) {
        // Only process if items exist
        if (!frm.doc.items || frm.doc.items.length === 0) {
            return;
        }

        frappe.confirm(
            __('Do you want to auto-generate Material Requests for shortage items grouped by GST rate?'),
            function () {
                // User confirmed - proceed with MR generation
                generate_gst_segregated_mrs(frm);
            }
        );
    }
});

/**
 * Main function to generate GST-segregated Material Requests
 */
async function generate_gst_segregated_mrs(frm) {
    frappe.dom.freeze(__('Analyzing items and generating Material Requests...'));

    try {
        // Step 1: Collect all required items (expand BOMs if needed)
        const required_items = await collect_required_items(frm);

        // Step 2: Check stock availability and calculate shortages
        const shortage_items = await calculate_shortages(required_items, frm);

        if (shortage_items.length === 0) {
            frappe.msgprint(__('All items are in stock. No Material Requests needed.'));
            frappe.dom.unfreeze();
            return;
        }

        // Step 3: Fetch GST rates for shortage items
        const items_with_gst = await fetch_gst_rates(shortage_items);

        // Step 4: Group items by GST rate
        const gst_groups = group_by_gst_rate(items_with_gst);

        // Step 5: Check for existing MRs (prevent duplicates)
        const existing_mrs = await check_existing_mrs(frm.doc.name);

        // Step 6: Create Material Requests per GST group
        await create_material_requests(gst_groups, frm, existing_mrs);

        frappe.msgprint({
            title: __('Success'),
            message: __('Material Requests created successfully for {0} GST group(s)', [Object.keys(gst_groups).length]),
            indicator: 'green'
        });

    } catch (error) {
        frappe.msgprint({
            title: __('Error'),
            message: __('Failed to generate Material Requests: {0}', [error.message]),
            indicator: 'red'
        });
        console.error('MR Generation Error:', error);
    } finally {
        frappe.dom.unfreeze();
    }
}

/**
 * Collect all required items (expand BOMs if present)
 */
async function collect_required_items(frm) {
    const required_items = [];

    for (const item_row of frm.doc.items) {
        // Check if item has BOM
        if (item_row.bom_no) {
            // Fetch BOM components
            const bom_items = await frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'BOM',
                    name: item_row.bom_no
                }
            });

            if (bom_items.message && bom_items.message.items) {
                for (const bom_item of bom_items.message.items) {
                    required_items.push({
                        item_code: bom_item.item_code,
                        qty: bom_item.qty * item_row.qty,
                        warehouse: frm.doc.set_warehouse,
                        uom: bom_item.uom,
                        schedule_date: item_row.delivery_date || frm.doc.delivery_date
                    });
                }
            }
        } else {
            // Regular item without BOM
            required_items.push({
                item_code: item_row.item_code,
                qty: item_row.qty,
                warehouse: frm.doc.set_warehouse,
                uom: item_row.uom,
                schedule_date: item_row.delivery_date || frm.doc.delivery_date
            });
        }
    }

    return required_items;
}

/**
 * Calculate shortages by checking stock availability
 */
async function calculate_shortages(required_items, frm) {
    const shortage_items = [];

    for (const item of required_items) {
        // Fetch current stock
        const stock_data = await frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Bin',
                filters: {
                    item_code: item.item_code,
                    warehouse: item.warehouse
                },
                fieldname: ['actual_qty', 'projected_qty']
            }
        });

        const available_qty = stock_data.message ? (stock_data.message.actual_qty || 0) : 0;
        const shortage_qty = item.qty - available_qty;

        if (shortage_qty > 0) {
            shortage_items.push({
                ...item,
                required_qty: item.qty,
                available_qty: available_qty,
                shortage_qty: shortage_qty
            });
        }
    }

    return shortage_items;
}

/**
 * Fetch GST rates for items from Item Master
 */
async function fetch_gst_rates(items) {
    const items_with_gst = [];

    for (const item of items) {
        // Fetch full Item document including taxes table
        const item_data = await frappe.call({
            method: 'frappe.client.get',
            args: {
                doctype: 'Item',
                name: item.item_code
            }
        });

        // Determine GST rate from Item Tax Template
        let gst_rate = 18; // Default

        if (item_data.message && item_data.message.taxes) {
            // Item has taxes child table
            for (const tax_row of item_data.message.taxes) {
                if (tax_row.item_tax_template) {
                    const template_name = tax_row.item_tax_template;

                    if (template_name.includes('5%') || template_name.includes('GST 5')) {
                        gst_rate = 5;
                        break;
                    } else if (template_name.includes('12%') || template_name.includes('GST 12')) {
                        gst_rate = 12;
                        break;
                    } else if (template_name.includes('18%') || template_name.includes('GST 18')) {
                        gst_rate = 18;
                        break;
                    } else if (template_name.includes('28%') || template_name.includes('GST 28')) {
                        gst_rate = 28;
                        break;
                    }
                }
            }
        }

        // Fallback: Check HSN code pattern for common solar items
        if (gst_rate === 18 && item_data.message && item_data.message.gst_hsn_code) {
            const hsn = item_data.message.gst_hsn_code;
            if (hsn.startsWith('8541') || hsn.startsWith('8504')) {
                gst_rate = 5; // Solar panels/inverters
            }
        }

        items_with_gst.push({
            ...item,
            gst_rate: gst_rate,
            item_name: item_data.message ? item_data.message.item_name : item.item_code
        });
    }

    return items_with_gst;
}

/**
 * Group items by GST rate
 */
function group_by_gst_rate(items) {
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
 * Check for existing Material Requests to prevent duplicates
 */
async function check_existing_mrs(sales_order) {
    const existing = await frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Material Request',
            filters: {
                custom_sales_order: sales_order
            },
            fields: ['name', 'custom_gst_rate']
        }
    });

    return existing.message || [];
}

/**
 * Create Material Requests for each GST group
 */
async function create_material_requests(gst_groups, frm, existing_mrs) {
    for (const [gst_rate, items] of Object.entries(gst_groups)) {
        // Check if MR already exists for this GST rate
        const exists = existing_mrs.find(mr => mr.custom_gst_rate == gst_rate);
        if (exists) {
            console.log(`MR already exists for GST ${gst_rate}%: ${exists.name}`);
            continue;
        }

        // Prepare Material Request document
        const mr_doc = {
            doctype: 'Material Request',
            material_request_type: 'Purchase',
            transaction_date: frappe.datetime.get_today(),
            schedule_date: frm.doc.delivery_date || frappe.datetime.add_days(frappe.datetime.get_today(), 7),
            company: frm.doc.company,
            set_warehouse: frm.doc.set_warehouse,
            custom_sales_order: frm.doc.name,
            custom_gst_rate: parseFloat(gst_rate),
            items: items.map(item => ({
                item_code: item.item_code,
                item_name: item.item_name,
                qty: item.shortage_qty,
                uom: item.uom,
                schedule_date: item.schedule_date,
                warehouse: item.warehouse
            })),
            custom_remarks: `Auto-generated from Sales Order ${frm.doc.name} | GST Group: ${gst_rate}%`
        };

        // Create the Material Request
        await frappe.call({
            method: 'frappe.client.insert',
            args: {
                doc: mr_doc
            },
            callback: function (r) {
                if (r.message) {
                    frappe.show_alert({
                        message: __('Created Material Request {0} for GST {1}%', [r.message.name, gst_rate]),
                        indicator: 'green'
                    }, 5);
                }
            }
        });
    }
}
