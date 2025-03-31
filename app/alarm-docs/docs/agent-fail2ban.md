## ALARM Fail2Ban Sync Script

This document explains the functionality of the Fail2Ban sync script, which ensures the local Fail2Ban service stays in sync with the ALARM blocklist.

---

## Purpose
- The script fetches the latest blocklist from the ALARM API.
- It applies new bans to Fail2Ban and removes unbanned IPs.
- It reports newly detected bans to the API.

---

## Steps Breakdown

### Step 1: Fetch Latest Blocklist
A `GET` request is made to `/api/blocklist/` to retrieve:

- `blocked_ips`: IPs that should be banned.
- `unblocked_ips`: IPs that should be removed from the ban list.

### Step 2: Apply Bans in Fail2Ban
For each IP in `blocked_ips`, the script runs:

```
fail2ban-client set sshd banip <IP>
```

### Step 3: Remove Unbanned IPs
For each IP in `unblocked_ips`, the script runs:

```
fail2ban-client set sshd unbanip <IP>
```

### Step 4: Report Newly Banned IPs to API
The script checks the currently banned IPs in Fail2Ban and reports any new bans to `/api/report_ban/`.

---

## Troubleshooting
Check logs at:

```
/var/log/alarm_agent_install.log
```
