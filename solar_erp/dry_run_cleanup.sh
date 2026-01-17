#!/bin/bash
# Test if the cleanup script will work correctly by doing a dry run

echo "=========================================="
echo "  DRY RUN - Git Cleanup Script"
echo "=========================================="
echo ""
echo "This is a DRY RUN - no files will be modified."
echo "It shows what WOULD be removed from Git tracking."
echo ""

# Count files
echo "📊 Files to remove from Git tracking:"
echo ""

# Build artifacts
if git ls-files | grep -q "public/build.json"; then
    echo "  ✓ public/build.json (build artifact)"
else
    echo "  ⊘ public/build.json (not currently tracked)"
fi

# Root-level patches
EMERGENCY_PATCHES=(
    "PATCH_auto_assign_vendor.py"
    "add_vendor_column.py"
    "disable_create_job_button.py"
    "emergency_fix_lead_vendor.py"
    "fix_assign_vendor_field.py"
    "fix_assigned_vendor_fields.py"
    "fix_workflow_status.py"
    "force_sync_schema.py"
    "manual_create_job_file.py"
    "patch_execution_workflow.py"
    "rename_workflow_state.py"
    "setup_execution_manager.py"
)

echo ""
echo "🚨 Emergency patches:"
tracked_count=0
for file in "${EMERGENCY_PATCHES[@]}"; do
    if git ls-files | grep -q "^$file$"; then
        echo "  ✓ $file"
        ((tracked_count++))
    else
        echo "  ⊘ $file (not tracked)"
    fi
done

# Setup scripts
SETUP_SCRIPTS=(
    "solar_erp/assign_gst_templates.py"
    "solar_erp/fix_brand_permissions.py"
    "solar_erp/fix_permissions.py"
    "solar_erp/fix_user_roles.py"
    "solar_erp/fix_workflow.py"
    "solar_erp/link_hsn_tax_templates.py"
    "solar_erp/make_territory_mandatory.py"
    "solar_erp/setup_purchase_gst.py"
    "solar_erp/setup_technical_survey.py"
)

echo ""
echo "🔧 Setup/fix scripts:"
for file in "${SETUP_SCRIPTS[@]}"; do
    if git ls-files | grep -q "^$file$"; then
        echo "  ✓ $file"
        ((tracked_count++))
    else
        echo "  ⊘ $file (not tracked)"
    fi
done

echo ""
echo "=========================================="
echo "📈 Summary:"
echo "  Total files currently tracked: $tracked_count"
echo "  Will be untracked by cleanup script"
echo "=========================================="
echo ""
echo "To see which files are currently tracked by Git:"
echo "  git ls-files | grep -E '(PATCH_|fix_|emergency_|patch_|setup_|build\.json)'"
