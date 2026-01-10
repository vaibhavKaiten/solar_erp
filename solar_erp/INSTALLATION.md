# Solar ERP - Installation Guide

This guide provides detailed instructions for installing the **Solar ERP** custom app on a new or existing ERPNext instance across **Windows**, **macOS**, and **Linux** platforms.

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
  - [Method 1: Install on Existing ERPNext Site](#method-1-install-on-existing-erpnext-site)
  - [Method 2: Fresh Installation with ERPNext](#method-2-fresh-installation-with-erpnext)
- [Platform-Specific Setup](#platform-specific-setup)
  - [Linux (Ubuntu/Debian)](#linux-ubuntudebian)
  - [macOS](#macos)
  - [Windows (WSL2)](#windows-wsl2)
- [Post-Installation Configuration](#post-installation-configuration)
- [Troubleshooting](#troubleshooting)
- [Updating the App](#updating-the-app)
- [Uninstallation](#uninstallation)

---

## 🔧 Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 4 GB | 8 GB+ |
| **Storage** | 10 GB | 20 GB+ |
| **CPU** | 2 cores | 4 cores+ |

### Software Requirements

- **Frappe Framework**: v14 or v15
- **ERPNext**: v14 or v15
- **Python**: 3.10 or 3.11
- **Node.js**: 16.x or 18.x
- **MariaDB**: 10.6+ or MySQL 8.0+
- **Redis**: 6.x or 7.x
- **nginx**: 1.18+ (for production)
- **Git**: 2.x

---

## 🚀 Installation Methods

### Method 1: Install on Existing ERPNext Site

If you already have a working ERPNext site, follow these steps:

#### Step 1: Navigate to Bench Directory

```bash
cd ~/frappe-bench
```

#### Step 2: Get the Solar ERP App

```bash
# From GitHub (replace with your repository URL)
bench get-app https://github.com/YOUR_USERNAME/solar_erp.git

# OR from a local directory
bench get-app /path/to/solar_erp
```

#### Step 3: Install on Your Site

```bash
# Replace 'your-site.local' with your actual site name
bench --site your-site.local install-app solar_erp
```

#### Step 4: Migrate Database

```bash
bench --site your-site.local migrate
```

#### Step 5: Clear Cache and Restart

```bash
# Clear cache
bench --site your-site.local clear-cache

# Rebuild assets
bench build --app solar_erp

# Restart bench
bench restart
```

#### Step 6: Verify Installation

```bash
# Check installed apps
bench --site your-site.local list-apps
```

You should see `solar_erp` in the list.

---

### Method 2: Fresh Installation with ERPNext

If you're setting up ERPNext from scratch, follow the platform-specific guides below.

---

## 🖥️ Platform-Specific Setup

### Linux (Ubuntu/Debian)

#### Prerequisites Installation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git python3-dev python3-pip python3-venv \
    redis-server mariadb-server nginx curl

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Yarn
sudo npm install -g yarn

# Install wkhtmltopdf (for PDF generation)
sudo apt install -y wkhtmltopdf
```

#### MariaDB Configuration

```bash
# Secure MariaDB installation
sudo mysql_secure_installation

# Configure MariaDB for Frappe
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
```

Add the following under `[mysqld]`:

```ini
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

Restart MariaDB:

```bash
sudo systemctl restart mariadb
```

#### Install Frappe Bench

```bash
# Install bench CLI
sudo pip3 install frappe-bench

# Initialize bench (Frappe v15 example)
bench init --frappe-branch version-15 frappe-bench

# Navigate to bench
cd frappe-bench
```

#### Create a New Site

```bash
# Create site
bench new-site your-site.local

# Install ERPNext
bench get-app erpnext --branch version-15
bench --site your-site.local install-app erpnext
```

#### Install Solar ERP

```bash
# Get Solar ERP
bench get-app https://github.com/YOUR_USERNAME/solar_erp.git

# Install on site
bench --site your-site.local install-app solar_erp

# Migrate
bench --site your-site.local migrate

# Set as default site (optional)
bench use your-site.local

# Start bench
bench start
```

Access your site at `http://localhost:8000`

---

### macOS

#### Prerequisites Installation

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required packages
brew install python@3.11 mariadb redis node@18 git

# Install wkhtmltopdf
brew install --cask wkhtmltopdf

# Install Yarn
npm install -g yarn
```

#### MariaDB Configuration

```bash
# Start MariaDB
brew services start mariadb

# Secure installation
mysql_secure_installation

# Configure MariaDB
nano /opt/homebrew/etc/my.cnf
```

Add the following:

```ini
[mysqld]
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

Restart MariaDB:

```bash
brew services restart mariadb
```

#### Install Frappe Bench

```bash
# Install bench
pip3 install frappe-bench

# Initialize bench
bench init --frappe-branch version-15 frappe-bench

# Navigate to bench
cd frappe-bench
```

#### Create Site and Install Apps

```bash
# Create site
bench new-site your-site.local

# Get ERPNext
bench get-app erpnext --branch version-15
bench --site your-site.local install-app erpnext

# Get Solar ERP
bench get-app https://github.com/YOUR_USERNAME/solar_erp.git
bench --site your-site.local install-app solar_erp

# Migrate
bench --site your-site.local migrate

# Start bench
bench start
```

Access at `http://localhost:8000`

---

### Windows (WSL2)

Frappe/ERPNext is not natively supported on Windows. Use **WSL2 (Windows Subsystem for Linux)**.

#### Step 1: Install WSL2

```powershell
# Run in PowerShell as Administrator
wsl --install -d Ubuntu-22.04
```

Restart your computer.

#### Step 2: Configure Ubuntu in WSL2

```bash
# Update Ubuntu
sudo apt update && sudo apt upgrade -y

# Follow the Linux (Ubuntu) installation steps above
```

#### Step 3: Access from Windows

After starting bench in WSL2, access the site from Windows browser at `http://localhost:8000`

**Note**: You can use **VS Code with WSL extension** for development.

---

## ⚙️ Post-Installation Configuration

### 1. Enable Developer Mode (Optional - for development)

```bash
bench --site your-site.local set-config developer_mode 1
bench --site your-site.local clear-cache
```

### 2. Create Administrator User

During site creation, you'll be prompted to create an admin user. If you need to reset the password:

```bash
bench --site your-site.local set-admin-password NEW_PASSWORD
```

### 3. Import Fixtures

Solar ERP automatically imports fixtures on installation. To manually re-import:

```bash
bench --site your-site.local migrate
bench --site your-site.local clear-cache
```

### 4. Setup Roles and Users

1. Login as Administrator
2. Go to **User** doctype
3. Create users and assign roles:
   - Sales Executive / Sales Manager
   - Vendor Executive / Vendor Manager
   - Project Manager
   - Inventory Manager
   - Purchase Manager
   - Technical Survey Executive / Manager
   - Installation Executives / Managers

### 5. Configure Suppliers and Territories

1. **Create Territories**: Setup → Territories
2. **Create Suppliers**: Buying → Supplier
3. **Link Suppliers to Territories**: In Supplier form, add territories in child table
4. **Create Vendor Users**: User doctype, assign Vendor Executive role
5. **Link Users to Suppliers**: Create Contact, link to Supplier and User

### 6. Setup Items and Tax Templates

1. **Create Items**: Stock → Item
2. **Setup GST Tax Templates**: Accounting → Item Tax Template
3. **Configure HSN Codes**: In Item master

### 7. Production Setup (Optional)

For production deployment:

```bash
# Setup production
sudo bench setup production YOUR_USER

# Enable HTTPS (optional)
sudo bench setup lets-encrypt your-site.local
```

---

## 🐛 Troubleshooting

### Issue: `bench: command not found`

**Solution**: Ensure bench is installed and in PATH

```bash
# Install bench
pip3 install frappe-bench

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH=$PATH:~/.local/bin
```

### Issue: MariaDB Connection Error

**Solution**: Check MariaDB is running and credentials are correct

```bash
# Check MariaDB status
sudo systemctl status mariadb

# Restart MariaDB
sudo systemctl restart mariadb

# Test connection
mysql -u root -p
```

### Issue: Port 8000 Already in Use

**Solution**: Kill existing process or use different port

```bash
# Find process using port 8000
sudo lsof -i :8000

# Kill process
kill -9 PID

# OR start on different port
bench serve --port 8001
```

### Issue: Assets Not Loading

**Solution**: Rebuild assets

```bash
bench build --app solar_erp
bench --site your-site.local clear-cache
bench restart
```

### Issue: Permission Denied Errors

**Solution**: Fix file permissions

```bash
cd ~/frappe-bench
chmod -R o+rx sites/
```

### Issue: Fixtures Not Imported

**Solution**: Manually trigger migration

```bash
bench --site your-site.local migrate
bench --site your-site.local clear-cache
bench restart
```

### Issue: Custom Fields Not Showing

**Solution**: Clear cache and reload

```bash
bench --site your-site.local clear-cache
# Reload browser with Ctrl+Shift+R (hard refresh)
```

---

## 🔄 Updating the App

### Update from Git Repository

```bash
cd ~/frappe-bench

# Pull latest changes
cd apps/solar_erp
git pull origin main
cd ../..

# Migrate
bench --site your-site.local migrate

# Clear cache and rebuild
bench --site your-site.local clear-cache
bench build --app solar_erp
bench restart
```

### Update Fixtures

If fixtures have been updated:

```bash
bench --site your-site.local migrate
bench --site your-site.local clear-cache
```

---

## 🗑️ Uninstallation

### Remove App from Site

```bash
# Uninstall from site
bench --site your-site.local uninstall-app solar_erp

# Remove app from bench (optional)
bench remove-app solar_erp
```

**Warning**: This will remove all Solar ERP data from the site. **Backup first!**

---

## 📦 Backup and Restore

### Create Backup

```bash
# Full backup (database + files)
bench --site your-site.local backup --with-files

# Backups are stored in: sites/your-site.local/private/backups/
```

### Restore Backup

```bash
# Restore database
bench --site your-site.local restore /path/to/backup.sql.gz

# Restore files
bench --site your-site.local restore --with-files /path/to/backup.tar
```

---

## 🔐 Security Best Practices

1. **Change default admin password** immediately after installation
2. **Enable HTTPS** for production sites
3. **Regular backups** - setup automated daily backups
4. **Update regularly** - keep Frappe, ERPNext, and Solar ERP updated
5. **Restrict database access** - don't expose MariaDB port publicly
6. **Use strong passwords** for all users
7. **Enable two-factor authentication** for admin users

---

## 📚 Additional Resources

- **Frappe Documentation**: https://frappeframework.com/docs
- **ERPNext Documentation**: https://docs.erpnext.com
- **Bench Documentation**: https://frappeframework.com/docs/user/en/bench
- **Frappe Forum**: https://discuss.erpnext.com

---

## 📞 Support

For Solar ERP specific issues:
- **Email**: hello@kaitensoftware.com
- **Publisher**: KaitenSoftware

For Frappe/ERPNext issues:
- **Frappe Forum**: https://discuss.erpnext.com
- **GitHub Issues**: https://github.com/frappe/frappe/issues

---

## ✅ Installation Checklist

- [ ] System prerequisites installed
- [ ] MariaDB configured and running
- [ ] Redis running
- [ ] Frappe bench initialized
- [ ] ERPNext installed
- [ ] Solar ERP app installed
- [ ] Database migrated
- [ ] Cache cleared
- [ ] Site accessible in browser
- [ ] Admin user created
- [ ] Custom roles assigned to users
- [ ] Suppliers and territories configured
- [ ] Items and tax templates setup
- [ ] Backup configured

---

**Last Updated**: January 2026
