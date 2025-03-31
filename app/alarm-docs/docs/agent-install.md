This document explains the steps that happens when the ALARM agent installation script is run.

---

## Prerequisites
- The script must be run as `root`
- The machine must have internet access to download required packages and register with the ALARM API
- The script accepts a `UNIQUE_ID` as a parameter for authentication with the API

---

## Steps Breakdown

### Step 1: Define Variables
The script defines important variables such as API URLs, token storage paths, log files, and system details.

### Step 2: Ensure Root Privileges
If the script is not run as `root`, it exits to prevent permission issues.

### Step 3: Create the `alarm-agent` User
A system user `alarm-agent` is created to run ALARM agent-related tasks.

!!! note
    This user account has login disabled.

### Step 4: Grant Required Permissions
The `alarm-agent` user is granted permission to:

- Restart the Vector service (`/bin/systemctl restart vector`)
    - This is required to update the tokens after a refresh
- Manage Fail2Ban (`/usr/bin/fail2ban-client`)

### Step 5: Detect Host IP Address
Retrieves the machine's primary IP address.

!!! note
    If detection fails, the script will exit under the assumption that there is a network error.

### Step 6: Install Required Packages
- **Fail2Ban**: Used to manage blocking of IPs and detecting brute-force attacks
- **jq**: Parses JSON responses
- **Vector**: Collects and forwards logs to the API

### Step 7: Register Device with API
The machine sends a registration request to `/api/register-device/` with:

- Hostname
- OS Information
- Unique Installation Token

The API returns access and refresh tokens for authentication.

### Step 8: Store Tokens Securely
- Tokens are stored in `/etc/alarm`, permissions `640` is set to restrict access
- The environment file `/etc/default/vector` is updated with the current access token

### Step 9: Configure Vector
A configuration file (`/etc/vector/vector.yaml`) is created to:

- Monitor authentication logs (`/var/log/auth.log`, `/var/log/secure`)
- Filter for successful/failed SSH login attempts
- Send logs securely to the ALARM API using a Bearer token

### Step 10: Enable & Start Vector Service
Ensures Vector starts on boot and is restarted immediately.

### Step 11: Create a Heartbeat Script
A heartbeat script (`/usr/local/bin/heartbeat.sh`) is created to:

- Send a heartbeat to the API
- Refresh expired tokens
- Restart Vector when new tokens are obtained

The script is then made executable.

### Step 12: Create Fail2Ban Sync Script
A fail2ban sync script (`/usr/local/bin/fail2ban_sync.sh`) is created to:

- Fetch the latest blocklist from the API
- Apply bans to Fail2Ban based on API-provided IPs
- Report newly banned IPs to the API

### Step 13: Create ALARM Sync Script
A final script is created that combines the heartbeat and Fail2Ban sync scripts into a single execution (`/usr/local/bin/alarm_sync.sh`).

### Step 14: Set Up Cron Job
A cron job is added for the `alarm-agent` user to run the sync script every 60 seconds.

!!! note
    This cron job is what informs how often the device will report its heartbeat to the API, and how often it will fetch an updated blocklist.

#### Change the heartbeat/sync interval
To alter how often the managed device will report back its heartbeat, and fetch the latest blocklist, you must edit the install script at the following location:

```
# Step 13: Add Single Cron Job for ALARM Sync
log "Setting up cron job for ALARM sync..."
(crontab -l 2>/dev/null | grep -v "heartbeat.sh" | grep -v "fail2ban_sync.sh"; echo "*/1 * * * * /bin/bash ${SYNC_ALL_SCRIPT}") | sort -u | sudo -u alarm-agent crontab -
```

Edit the crontab entry to run as often as you desire.

!!! warning
    The dashboard will report a degraded connection to a managed device if it doesn't check-in with a hearbeat in more than 5 minutes, it will report a failed conenction after 1 hour without a heartbeat.

### Step 15: Configure Fail2Ban for SSH Protection
Creates a jail configuration (`/etc/fail2ban/jail.local`) to:

- Ban IPs after 5 failed login attempts
- Apply an infinite ban to the IP

!!! note
    IPs can only be unblocked via the dashboard, individual managed devices will not unban an IP after any length of time.

### Step 16: Restart Fail2Ban
Ensures Fail2Ban is restarted with the new configuration.

### Step 17: Final Confirmation
Logs completion and exits successfully.

---

## Troubleshooting
If the installer fails to complete, see the log that was generated at:

```
/var/log/alarm_agent_install.log
```

Any issues it encounters will be documented here.

