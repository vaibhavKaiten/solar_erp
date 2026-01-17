frappe.ui.form.on("Product Bundle", {
    refresh(frm) {
        // Disable new_item_code after save
        frm.toggle_enable("new_item_code", frm.is_new());

        // Set query filter for new_item_code
        frm.set_query("new_item_code", () => {
            return {
                filters: {
                    item_group: "Products"
                }
            };
        });
    },

    // new_item_code(frm) {
    //     // Trigger when new_item_code changes
    //     if (!frm.doc.new_item_code) return;

    //     frappe.call({
    //         method: "solar_erp.solar_project.custom.py.bundle.get_bom_items",
    //         args: {
    //             item_code: frm.doc.new_item_code
    //         },
    //         callback(r) {
    //             if (r.message && r.message.length > 0) {
    //                 // clear old entries
    //                 frm.clear_table("items");

    //                 // add BOM items
    //                 r.message.forEach(row => {
    //                     let d = frm.add_child("items");
    //                     d.item_code = row.item_code;
    //                     d.description = row.description;
    //                     d.qty = row.qty;
    //                     d.uom = row.uom;
    //                 });

    //                 frm.refresh_field("items");
    //                 frappe.show_alert({
    //                     message: __('BOM items loaded successfully'),
    //                     indicator: 'green'
    //                 }, 3);
    //             } else {
    //                 frappe.msgprint({
    //                     title: __('No BOM Found'),
    //                     message: __('No default BOM found for item {0}', [frm.doc.new_item_code]),
    //                     indicator: 'orange'
    //                 });
    //             }
    //         },
    //         error(r) {
    //             frappe.msgprint({
    //                 title: __('Error'),
    //                 message: __('Failed to fetch BOM items'),
    //                 indicator: 'red'
    //             });
    //         }
    //     });
    // }
});
