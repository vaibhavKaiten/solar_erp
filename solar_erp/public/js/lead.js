/**
 * Client-side logic for Lead DocType - Vendor Assignment Fields
 * Handles vendor field filtering based on Territory
 */

frappe.ui.form.on('Lead', {
    refresh: function(frm) {
        setup_vendor_fields(frm);
    },
    
    // When Assignment Territory changes
    custom_territory_display: function(frm) {
        handle_territory_change(frm);
    },
    
    // When standard territory changes (fallback)
    territory: function(frm) {
        if (!frm.doc.custom_territory_display) {
            handle_territory_change(frm);
        }
    }
});

/**
 * Get the territory value from custom or standard field
 */
function get_territory_value(frm) {
    return frm.doc.custom_territory_display || frm.doc.territory;
}

/**
 * Handle territory change - clear vendor fields and re-setup
 */
function handle_territory_change(frm) {
    const territory = get_territory_value(frm);
    
    // Clear vendor fields when territory changes
    if (frm.doc.vendor_assign || frm.doc.meter_execution_vendor) {
        frm.set_value('vendor_assign', '');
        frm.set_value('meter_execution_vendor', '');
    }
    
    // Re-setup the fields
    setup_vendor_fields(frm);
}

/**
 * Setup vendor fields with proper filtering based on territory
 */
function setup_vendor_fields(frm) {
    const territory = get_territory_value(frm);
    
    if (!territory) {
        // Territory not selected - fields will be hidden by depends_on
        return;
    }
  
    if (frm.fields_dict.vendor_assign) {
        frm.set_query('vendor_assign', function() {
            return {
                query: 'solar_erp.solar_erp.api.lead_vendor.get_technical_vendors',
                filters: {
                    'territory': territory
                }
            };
        });
        
        frm.set_df_property('vendor_assign', 'description', 
            'Select Survey Vendor assigned to ' + territory);
    }
    
  
    if (frm.fields_dict.meter_execution_vendor) {
        frm.set_query('meter_execution_vendor', function() {
            return {
                query: 'solar_erp.solar_erp.api.lead_vendor.get_meter_vendors',
                filters: {
                    'territory': territory
                }
            };
        });
        
        frm.set_df_property('meter_execution_vendor', 'description',
            'Select Meter Vendor assigned to ' + territory);
    }
}
