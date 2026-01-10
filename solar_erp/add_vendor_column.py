"""
Check correct table names and add assigned_vendor column
"""
import frappe

print("\n🔍 Checking and Adding assigned_vendor Column...\n")

doctypes = [
    "Technical Survey",
    "Structure Mounting",
    "Project Installation",
    "Meter Installation",
    "Meter Commissioning",
    "Verification Handover"
]

for doctype in doctypes:
    try:
        # Get the correct table name from meta
        meta = frappe.get_meta(doctype)
        
        # Check if column exists
        columns = frappe.db.sql(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'tab{doctype}'
            AND COLUMN_NAME = 'assigned_vendor'
        """, as_dict=True)
        
        if columns:
            print(f"✅ {doctype}: assigned_vendor column already exists")
        else:
            print(f"⚠️  {doctype}: assigned_vendor column NOT found, adding...")
            
            # Add the column
            frappe.db.sql(f"""
                ALTER TABLE `tab{doctype}` 
                ADD COLUMN `assigned_vendor` VARCHAR(140) NULL
            """)
            frappe.db.commit()
            print(f"✅ {doctype}: assigned_vendor column added successfully")
            
    except Exception as e:
        print(f"❌ {doctype}: Error - {str(e)}")
        frappe.db.rollback()
    
    print()

print("✅ Column addition completed!\n")
