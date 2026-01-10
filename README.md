# Solar ERP

> **A comprehensive Solar Project Management System built on Frappe/ERPNext**

Solar ERP is a custom Frappe application designed to streamline and automate the complete lifecycle of solar panel installation projects—from lead generation to final verification and handover. Built by **KaitenSoftware**, this app extends ERPNext with specialized modules for solar project execution, vendor management, procurement consolidation, and financial workflows.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Repository Structure](#repository-structure)
- [Modules](#modules)
- [Core Workflows](#core-workflows)
- [Custom DocTypes](#custom-doctypes)
- [Installation](#installation)
- [Configuration](#configuration)
- [Development](#development)
- [License](#license)

---

## 🌟 Overview

Solar ERP is designed to manage the entire solar installation business process with role-based access control, automated workflows, and real-time tracking. The system supports:

- **Multi-vendor execution** with territory-based vendor assignment
- **Linear execution workflow** ensuring proper stage progression
- **Automated procurement consolidation** with GST-aware material request handling
- **BOM-based stock reservation** for Sales Orders
- **Advance payment gates** for execution stages
- **Comprehensive role management** (Sales, Vendor, Project Manager, Inventory, etc.)

---

## ✨ Key Features

### 1. **Lead-to-Job Workflow**
- Automated lead qualification and vendor assignment
- Territory-based vendor filtering
- Opportunity and Customer creation from Leads
- Seamless transition from Sales to Execution

### 2. **Execution Management**
Six-stage linear execution workflow:
1. **Technical Survey** - Site assessment and BOM creation
2. **Structure Mounting** - Foundation and structure installation
3. **Panel Installation** - Solar panel mounting
4. **Meter Installation** - Meter setup
5. **Meter Commissioning** - System activation
6. **Verification Handover** - Final inspection and handover

Each stage includes:
- Status-based action buttons (Start, Hold, Submit, Approve, Rework, Close, Reopen)
- Role-based permissions (Vendor Executive vs Project Manager)
- Automatic next-stage creation on approval
- Photo logs and revisit tracking

### 3. **Procurement Consolidation**
- Fetch and consolidate approved Material Requests
- Group items by Item Code with total quantities
- Dual-quantity system (Required Qty vs Actual Qty)
- Multi-supplier Purchase Order creation
- Automatic quantity reconciliation after PO creation
- GST-aware Material Request splitting

### 4. **BOM & Stock Management**
- Automatic BOM creation from Sales Orders
- Stock reservation for BOM items
- Shortage tracking and Material Request generation
- Purchase Receipt integration for stock replenishment

### 5. **Vendor Management**
- Supplier-User linking via Contact
- Territory-based vendor activation
- Automatic vendor assignment in execution stages
- Vendor portal access for field staff

### 6. **Financial Controls**
- Advance payment verification gates
- Payment Entry integration with Sales Orders
- Delivery Note automation on payment
- GST calculation and tax template management

---

## 📁 Repository Structure

```
solar_erp/
├── solar_erp/                    # Main module (Solar ERP)
│   ├── doctype/                  # Custom DocTypes
│   │   ├── job_file/             # Central job coordination
│   │   ├── technical_survey/     # Stage 1: Site survey
│   │   ├── structure_mounting/   # Stage 2: Structure work
│   │   ├── panel_installation/   # Stage 3: Panel mounting (future)
│   │   ├── meter_installation/   # Stage 4: Meter setup
│   │   ├── meter_commissioning/  # Stage 5: System activation
│   │   ├── verification_handover/# Stage 6: Final handover
│   │   ├── procurement_consolidation/  # Procurement management
│   │   ├── photo_log/            # Photo documentation
│   │   ├── revisit_log/          # Revisit tracking
│   │   └── [other child tables]  # BOM items, stock logs, etc.
│   ├── api/                      # Server-side business logic
│   │   ├── execution_workflow.py # Execution stage validation
│   │   ├── execution_actions.py  # Status transition actions
│   │   ├── lead_vendor.py        # Lead-vendor assignment
│   │   ├── bom_stock_reservation.py  # Stock management
│   │   ├── quotation_workflow.py # Quotation automation
│   │   ├── advance_payment.py    # Payment processing
│   │   ├── material_request_validation.py  # MR validation
│   │   ├── purchase_gst_hook.py  # GST calculation
│   │   ├── sales_order_bom.py    # BOM generation
│   │   ├── technical_survey.py   # Survey-specific logic
│   │   └── supplier_portal.py    # Vendor portal APIs
│   ├── doc_events/               # Document event handlers
│   │   ├── lead_events.py        # Lead validation & updates
│   │   ├── contact_events.py     # Contact-Supplier linking
│   │   └── delivery_note_events.py  # Delivery automation
│   ├── permissions/              # Custom permission controllers
│   │   └── technical_survey_permissions.py
│   ├── custom_fields/            # Custom field definitions
│   ├── utils/                    # Utility functions
│   └── scripts/                  # Maintenance & migration scripts
├── solar_project/                # Secondary module (legacy/additional)
│   ├── doctype/                  # Additional DocTypes
│   │   ├── bank_loan_application/
│   │   ├── discom_process/
│   │   └── subsidy_application/
│   ├── custom/                   # Custom JS overrides
│   │   └── js/
│   └── tasks.py                  # Scheduled tasks
├── fixtures/                     # Exportable configuration
│   ├── custom_field.json         # Custom fields (149KB)
│   ├── client_script.json        # Client-side scripts
│   ├── server_script.json        # Server-side scripts
│   ├── workflow.json             # Workflow definitions
│   ├── workflow_state.json       # Workflow states
│   ├── workflow_action_master.json
│   ├── role.json                 # Custom roles
│   └── property_setter.json      # Property overrides
├── public/                       # Static assets
│   └── js/                       # Client-side JavaScript
│       ├── execution_common.js   # Shared execution UI logic
│       ├── lead.js               # Lead form customizations
│       ├── quotation.js          # Quotation enhancements
│       ├── sales_order_mr.js     # Sales Order MR button
│       ├── material_request_gst.js  # MR GST split
│       ├── sales_invoice.js      # Invoice customizations
│       └── supplier.js           # Supplier form enhancements
├── templates/                    # Jinja templates
│   └── pages/                    # Custom pages
├── config/                       # App configuration
├── hooks.py                      # Frappe hooks (fixtures, events, permissions)
├── modules.txt                   # Module list
├── patches.txt                   # Database patches
├── __init__.py
├── README.md                     # This file
└── INSTALLATION.md               # Setup guide
```

---

## 🧩 Modules

### 1. **Solar ERP** (Main Module)
Core execution, procurement, and workflow management.

**Key DocTypes:**
- Job File
- Technical Survey
- Structure Mounting
- Panel Installation
- Meter Installation
- Meter Commissioning
- Verification Handover
- Procurement Consolidation
- Photo Log
- Revisit Log

### 2. **Solar Project** (Secondary Module)
Additional processes and legacy features.

**Key DocTypes:**
- Bank Loan Application
- DISCOM Process
- Subsidy Application

---

## 🔄 Core Workflows

### Lead to Job Workflow

```
Lead (Draft)
  ↓ [Mark Contacted]
Lead (Contacted)
  ↓ [Mark Qualified]
Lead (Qualified)
  ↓ [Initiate Job]
  ├─→ Opportunity (Created)
  ├─→ Customer (Created)
  └─→ Job File (Created)
```

### Sales to Execution Workflow

```
Quotation
  ↓ [Submit]
Sales Order (Created)
  ↓ [Auto BOM Creation]
BOM Items Reserved
  ↓ [Check Stock]
Material Request (if shortage)
  ↓ [Procurement]
Purchase Order → Purchase Receipt
  ↓ [Payment Entry]
Advance Payment Verified
  ↓ [Auto Create]
Technical Survey (Stage 1)
```

### Execution Stage Workflow

```
Draft
  ↓ [Vendor: Start]
In Progress
  ↓ [Vendor: Submit for Review]
Ready for Review / In Review / Submitted
  ↓ [Manager: Approve]
Approved
  ↓ [Auto Create Next Stage]
Next Stage (Draft)

Alternative paths:
- [Vendor: Hold] → On Hold → [Manager: Reopen] → Reopened
- [Manager: Request Rework] → Rework → [Vendor: Start] → In Progress
- [Manager: Close] → Closed
```

### Procurement Consolidation Workflow

```
Procurement Consolidation (Draft)
  ↓ [Fetch Approved Material Requests]
Items Consolidated (Required Qty set)
  ↓ [User edits Actual Qty]
  ↓ [Select Supplier]
  ↓ [Create Purchase Order]
Purchase Order (Draft) created
  ↓ [System reconciles quantities]
Required Qty reduced by Actual Qty
Items marked complete when Required Qty = 0
```

---

## 📦 Custom DocTypes

### Execution DocTypes
| DocType | Purpose | Key Fields |
|---------|---------|------------|
| **Job File** | Central job coordination | `sales_order`, `customer`, `territory`, `assigned_vendor` |
| **Technical Survey** | Site assessment | `job_file`, `assigned_vendor`, `status`, `survey_start_date`, BOM items |
| **Structure Mounting** | Foundation work | `job_file`, `linked_technical_survey`, `status` |
| **Panel Installation** | Panel mounting | `job_file`, `linked_structure_mounting`, `status` |
| **Meter Installation** | Meter setup | `job_file`, `linked_panel_installation`, `status` |
| **Meter Commissioning** | System activation | `job_file`, `linked_meter_installation`, `status` |
| **Verification Handover** | Final handover | `job_file`, `linked_meter_commissioning`, `status` |

### Procurement DocTypes
| DocType | Purpose | Key Fields |
|---------|---------|------------|
| **Procurement Consolidation** | MR consolidation | `items` (child table), `fetch_approved_material_requests` (button) |
| **Consolidated Procurement Item** | Child table | `item_code`, `total_required_quantity`, `actual_quantity`, `is_completed`, `supplier`, `gst_rate` |

### Supporting DocTypes
| DocType | Purpose |
|---------|---------|
| **Photo Log** | Photo documentation for execution stages |
| **Revisit Log** | Track revisits and rework |
| **Stock Reservation Log** | BOM stock reservation tracking |
| **Procurement Shortage Log** | Material shortage tracking |
| **Various BOM Item tables** | Child tables for BOM items in different stages |

---

## 🛠️ Installation

For detailed installation instructions for **Windows**, **Mac**, and **Linux**, please refer to:

👉 **[INSTALLATION.md](https://github.com/vaibhavKaiten/solar_erp/blob/main/solar_erp/INSTALLATION.md)**

### Quick Start (Existing ERPNext Site)

```bash
# Navigate to your Frappe bench
cd ~/frappe-bench

# Get the app from GitHub
bench get-app https://github.com/YOUR_USERNAME/solar_erp.git

# Install on your site
bench --site your-site.local install-app solar_erp

# Migrate database
bench --site your-site.local migrate

# Clear cache
bench --site your-site.local clear-cache

# Restart bench
bench restart
```

---

## ⚙️ Configuration

### 1. **Import Fixtures**
After installation, fixtures are automatically imported. These include:
- Custom Fields
- Client Scripts
- Server Scripts
- Workflows and Workflow States
- Custom Roles
- Property Setters

### 2. **Role Assignment**
Assign users to custom roles:
- Sales Executive / Sales Manager
- Vendor Executive / Vendor Manager
- Project Manager
- Inventory Manager / Purchase Manager
- Technical Survey Executive / Manager
- Installation Executives / Managers
- Discom Executive
- Subsidy Executive
- Loan Process Executive

### 3. **Supplier Setup**
- Create Suppliers for vendors
- Link Suppliers to Territories
- Create Users for vendor staff
- Link Users to Suppliers via Contact

### 4. **Territory Configuration**
- Define Territories (e.g., Jaipur, Udaipur, Delhi)
- Assign Suppliers to Territories
- Configure territory-based filtering

### 5. **Item and BOM Setup**
- Create Items for solar components
- Set up GST Tax Templates
- Configure HSN codes
- Define default suppliers

---

## 👨‍💻 Development

### Prerequisites
- Frappe Framework (v14 or v15)
- ERPNext (v14 or v15)
- Python 3.10+
- Node.js 16+
- MariaDB 10.6+

### Development Workflow

```bash
# Enable developer mode
bench --site your-site.local set-config developer_mode 1

# Watch for changes
bench watch

# Run in development mode
bench start

# Export fixtures after changes
bench --site your-site.local export-fixtures
```

### Key Development Files

- **hooks.py**: Register fixtures, doc_events, permissions, scheduled tasks
- **public/js/execution_common.js**: Shared UI logic for execution stages
- **api/execution_workflow.py**: Stage validation and vendor assignment
- **api/execution_actions.py**: Status transition logic
- **fixtures/**: Configuration exports (custom fields, scripts, workflows)

### Adding New Execution Stages

1. Create new DocType in `solar_erp/doctype/`
2. Add status field with standard values
3. Add `job_file` and `assigned_vendor` link fields
4. Register in `hooks.py` under `doc_events`
5. Add client script using `solar_erp.execution` namespace
6. Update `execution_common.js` role maps if needed

---

## 📚 Documentation

### Additional Documentation Files

- **[INSTALLATION.md](./INSTALLATION.md)** - Detailed setup guide for all platforms
- **PROCUREMENT_CONSOLIDATION_DOCTYPE.md** - Procurement consolidation details
- **GST_MR_SEGREGATION_DOCS.md** - GST-based Material Request splitting
- **HOW_TERRITORY_FILTERING_WORKS.md** - Territory-based vendor filtering
- **LEAD_WORKFLOW_ERRORS_FIXED.md** - Lead workflow troubleshooting
- **TASK_COMPLETE_*.md** - Feature implementation documentation

---

## 🔐 Security & Permissions

### Permission Controllers
- **Technical Survey**: Custom query conditions and has_permission checks
- Territory-based record filtering
- Vendor Executive can only see assigned records
- Project Manager has full visibility

### Role Hierarchy
```
System Manager (Full Access)
  ├─ Project Manager (Execution oversight)
  ├─ Sales Manager (Lead & Sales)
  ├─ Vendor Manager (Vendor coordination)
  ├─ Purchase Manager (Procurement)
  └─ Inventory Manager (Stock)
      ├─ Sales Executive
      ├─ Vendor Executive
      ├─ Technical Survey Executive
      └─ [Other Executives]
```

---

## 🧪 Testing

### Manual Testing Checklist
- [ ] Lead creation and vendor assignment
- [ ] Quotation to Sales Order flow
- [ ] BOM creation and stock reservation
- [ ] Material Request generation
- [ ] Procurement Consolidation
- [ ] Execution stage progression
- [ ] Advance payment gate
- [ ] Photo log and revisit tracking

### Automated Tests
(To be implemented)

---

## 🐛 Known Issues & Limitations

1. **Panel Installation** doctype is referenced but may not be fully implemented
2. **Workflow State** transitions require careful role assignment
3. **Stock Reservation** logic assumes BOM items are available
4. **GST Calculation** requires proper tax template setup

---

## 🤝 Contributing

This is a proprietary application developed by **KaitenSoftware**. For contributions or issues, please contact the development team.

---

## 📄 License

**MIT License**

Copyright (c) 2025 KaitenSoftware

---

## 📞 Support

- **Email**: hello@kaitensoftware.com
- **Publisher**: KaitenSoftware
- **App Version**: Check `hooks.py` for current version

---

## 🙏 Acknowledgments

Built on the powerful **Frappe Framework** and **ERPNext** platform.

---

**Last Updated**: January 2026
