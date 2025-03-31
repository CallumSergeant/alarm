# ALARM Dashboard Documentation

This document provides an overview of the various dashboard views available in the ALARM project. These views enable users to monitor login attempts, manage devices, configure system settings, and review alerts.

---

##  Dashboard Home
### **View:** `dashboard_home`
**Template:** `dashboard/dashboard_home.html`

**Description:**
Displays an overview of failed and successful login attempts, insights, and top login sources over different time periods.

**Key Data Displayed:**
- Failed logins (last 24 hours, last week, all-time)
- Successful logins (last 24 hours, last week, all-time)
- Top failed/successful login sources
- Hourly login trends for visualisation
- Security insights based on login patterns

---

##  Login Attempt List
### **View:** `login_attempt_list`
**Template:** `dashboard/login_attempt_list.html`

**Description:**
Provides a paginated list of login attempts with filtering options.

**Filters Available:**
- **Search Query (`q`)**: Filter by IP address or action (failed/successful login)
- **Start Date (`start_datetime`)**: Filter logins from a specific timestamp
- **End Date (`end_datetime`)**: Filter logins up to a specific timestamp

**Pagination:**
- Displays 15 login attempts per page

---

##  Blocked IPs Management
### **View:** `blocked_ips`
**Template:** `dashboard/blocked_ips.html`

**Description:**
Displays a list of blocked IPs with search and filter options. Allows manually blocking new IPs.

**Filters Available:**
- **Search Query (`q`)**: Filter by IP address or reason
- **Start Date (`start_datetime`)**: Filter blocked IPs from a specific date
- **End Date (`end_datetime`)**: Filter blocked IPs up to a specific date

**Manual IP Blocking:**
- Users can submit an IP address with an optional reason to block it.
- Invalid IP formats will show an error message.

---

##  Toggle IP Ban Status
### **View:** `toggle_ban_ip`
**Template:** Uses `redirect("blocked-ips")`

**Description:**
Toggles the ban status of a given IP address when a POST request is made.

**Behavior:**
- If an IP is currently banned, it will be unbanned.
- If an IP is not banned, it will be marked as banned.
- Redirects back to the blocked IPs page after updating.

---

##  Alerts View
### **View:** `alerts_view`
**Template:** `dashboard/alerts.html`

**Description:**
Displays a list of security alerts with filtering options.

**Filters Available:**
- **Search Query (`q`)**: Filter by title or message
- **Start Date (`start_datetime`)**: Filter alerts from a specific timestamp
- **End Date (`end_datetime`)**: Filter alerts up to a specific timestamp
- **Severity (`severity`)**: Filter alerts by severity (INFO, WARNING, ERROR, etc.)

**Pagination:**
- Displays 15 alerts per page

---

##  System Settings
### **View:** `system_settings`
**Template:** `dashboard/system_settings.html`

**Description:**
Allows administrators to update and manage system installation/uninstallation scripts.

**Actions:**
- Users can edit and save the install and uninstall scripts.
- Scripts are stored in the database and updated on submission.
- Successful updates trigger an alert message.

---

##  Managed Devices
### **View:** `managed_devices`
**Template:** `dashboard/managed_devices.html`

**Description:**
Displays a paginated list of all registered devices along with their last check-in time.

**Displayed Data:**
- Device hostname
- Last check-in time
- Status based on time since last check-in

**Pagination:**
- Displays 10 devices per page

---

##  Get System Script
### **View:** `get_script`
**Response Type:** `text/plain` (file download)

**Description:**
Fetches and downloads a system script (install/uninstall) based on the provided script type.

**Response Headers:**
- `Content-Disposition: attachment; filename="install_script.sh"`
- `Content-Type: text/plain`

---

##  Generate Install Command
### **View:** `generate_install_command`
**Response Type:** `JSON`

**Description:**
Generates a unique install token and returns the installation command for a new device.

**Example Response:**
```json
{
    "command": "curl -sSL https://alarm.sgt.me.uk/install.sh | sudo bash -s -- abc123",
    "token": "abc123"
}
```

---