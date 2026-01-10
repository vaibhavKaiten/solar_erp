"""
Custom Query Methods for Solar ERP
"""

import frappe


@frappe.whitelist()
def get_vendor_executives(doctype, txt, searchfield, start, page_len, filters):
    """
    Get vendor executives from the same supplier company
    
    This query is used in the custom_technical_executive field to show only
    users who belong to the same vendor company as the assigned_vendor.
    
    Args:
        doctype: Target doctype (not used)
        txt: Search text
        searchfield: Field to search in
        start: Pagination start
        page_len: Number of results per page
        filters: Dict with 'vendor_company' key
    
    Returns:
        List of tuples: [(user_email, user_full_name), ...]
    """
    vendor_company = filters.get('vendor_company')
    
    if not vendor_company:
        return []
    
    # Get all contacts linked to this supplier via Dynamic Link
    contacts = frappe.db.sql("""
        SELECT dl.parent
        FROM `tabDynamic Link` dl
        WHERE dl.link_doctype = 'Supplier'
            AND dl.link_name = %(vendor_company)s
            AND dl.parenttype = 'Contact'
    """, {'vendor_company': vendor_company}, as_dict=True)
    
    contact_names = [c.parent for c in contacts]
    
    if not contact_names:
        return []
    
    # Get users with Vendor Executive role from these contacts
    return frappe.db.sql("""
        SELECT DISTINCT u.name, u.full_name
        FROM `tabUser` u
        INNER JOIN `tabContact` c ON c.user = u.name
        INNER JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE hr.role = 'Vendor Executive'
            AND c.name IN %(contacts)s
            AND u.enabled = 1
            AND (u.name LIKE %(txt)s OR u.full_name LIKE %(txt)s)
        ORDER BY u.full_name
        LIMIT %(start)s, %(page_len)s
    """, {
        'contacts': contact_names,
        'txt': f'%{txt}%',
        'start': start,
        'page_len': page_len
    })
