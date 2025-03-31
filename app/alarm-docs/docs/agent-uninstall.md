## ALARM Agent Uninstallation Process

This document explains the steps that occur when the ALARM agent uninstallation script is run.

---

## Prerequisites
- The script must be run as `root`
- The machine must have been previously registered with the ALARM system
- The script will attempt to deregister the device from the ALARM API

---

## Steps Breakdown

### Step 1: Stop and Disable Vector Service
The script ensures that Vector is stopped and disabled to prevent any further log collection.

### Step 2: Remove Vector
Vector is uninstalled from the system, along with any unnecessary dependencies.

### Step 3: Remove Fail2Ban
Fail2Ban is removed, ensuring that the system no longer enforces bans based on ALARM’s centralized blocklist.

### Step 4: Remove `jq`
The `jq` package, which was used for JSON parsing, is removed.

### Step 5: Deregister Device from API
If an access token is found, the script sends a `DELETE` request to `/api/deregister/` to inform the ALARM API that the device is being removed.

!!! note
    If the access token is missing or expired, deregistration is skipped.

### Step 6: Remove Vector Configuration
Deletes the Vector configuration file (`/etc/vector/vector.yaml`).

### Step 7: Remove Tokens and Environment File
- The ALARM token directory (`/etc/alarm`) is removed
- The Vector environment file (`/etc/default/vector`) is deleted

### Step 8: Remove Heartbeat Script
The heartbeat script (`/usr/local/bin/heartbeat.sh`), which was responsible for keeping the device in sync with the ALARM API, is deleted.

### Step 9: Remove Heartbeat Cron Job
The cron job that executed the heartbeat script is removed from the `alarm-agent` user's crontab.

### Step 10: Remove `alarm-agent` sudoers Entry
The `alarm-agent` user was granted specific permissions for managing Vector and Fail2Ban. This entry is now removed from the `/etc/sudoers.d/` directory.

### Step 11: Remove `alarm-agent` User
The `alarm-agent` system user is removed, along with its home directory.

!!! note
    Any remaining files owned by `alarm-agent` that were not removed by previous steps may still exist.

### Step 12: Clean Up Logs
The installation log file (`/var/log/alarm_agent_install.log`) is deleted to remove traces of the initial setup.

### Step 13: Final Confirmation
Logs the completion of the uninstallation and exits successfully.

---

## Troubleshooting
If the uninstaller encounters issues, check the log file at:

```
/var/log/alarm_agent_uninstall.log
```

All uninstallation steps and any errors encountered will be recorded there.
