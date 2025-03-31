## ALARM Sync Script

This document explains the functionality of the ALARM sync script, which ensures that the system periodically sends a heartbeat and updates Fail2Ban rules.

---

## Purpose
- The script runs both the heartbeat script and the Fail2Ban sync script in a single execution.
- It is executed periodically by a cron job.

---

## Steps Breakdown

### Step 1: Execute Heartbeat Script
Runs:

```
/usr/local/bin/heartbeat.sh
```

### Step 2: Execute Fail2Ban Sync Script
Runs:

```
/usr/local/bin/fail2ban_sync.sh
```

---

## Cron Job Execution
This script is executed every 60 seconds by a cron job under the `alarm-agent` user.

To modify the interval, update the crontab entry:

```
*/1 * * * * /bin/bash /usr/local/bin/alarm_sync.sh
```

!!! warning
    If a managed device does not check in with a heartbeat within 5 minutes, the dashboard will report a degraded connection. After 1 hour of no heartbeat, it will report a failed connection.

---

## Troubleshooting
If synchronisation fails, check:

```
/var/log/alarm_agent_install.log
```
