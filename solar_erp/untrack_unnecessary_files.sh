#!/bin/bash
# ============================================================================
# Git Cleanup Script - Remove unnecessary files from version control
# ============================================================================
# This script removes one-time patches, emergency fixes, and build artifacts
# from Git tracking while preserving them locally (if needed for reference)
#
# Usage: bash untrack_unnecessary_files.sh
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "  Solar ERP - Git Cleanup Script"
echo "============================================================================"
echo ""
echo "This will remove the following categories from Git tracking:"
echo "  1. Build artifacts (public/build.json)"
echo "  2. One-time emergency patches (PATCH_*.py, fix_*.py, etc.)"
echo "  3. Root-level setup scripts (moved to patches/)"
echo ""
echo "Files will remain in your working directory but won't be tracked by Git."
echo ""

# Confirm before proceeding
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Starting cleanup..."
echo ""

# ============================================================================
# 1. Build Artifacts
# ============================================================================
echo "📦 Removing build artifacts..."
git rm --cached -f public/build.json 2>/dev/null || echo "  (public/build.json not tracked)"

# ============================================================================
# 2. Root-Level Emergency Patches
# ============================================================================
echo ""
echo "🚨 Removing root-level emergency patches..."

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

for file in "${EMERGENCY_PATCHES[@]}"; do
    git rm --cached -f "$file" 2>/dev/null || echo "  ($file not tracked)"
done

# ============================================================================
# 3. Root-Level Setup Scripts (should be in patches/)
# ============================================================================
echo ""
echo "🔧 Removing root-level setup scripts from solar_erp/..."

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

for file in "${SETUP_SCRIPTS[@]}"; do
    git rm --cached -f "$file" 2>/dev/null || echo "  ($file not tracked)"
done

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "============================================================================"
echo "✅ Cleanup Complete!"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Commit the removal: git commit -m 'chore: remove build artifacts and one-time patches from version control'"
echo "  3. Push to remote: git push"
echo ""
echo "Note: Files still exist locally but are now in .gitignore"
echo "============================================================================"
