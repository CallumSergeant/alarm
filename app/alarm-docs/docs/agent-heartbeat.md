## ALARM Heartbeat Script

This document explains the functionality of the heartbeat script, which ensures that the ALARM agent maintains a connection with the ALARM API.

---

## Purpose
- The script periodically sends a heartbeat signal to the ALARM API.
- If the access token has expired, the script attempts to refresh it.
- If a new token is obtained, the Vector service is restarted with the updated credentials.

---

## Steps Breakdown

### Step 1: Read Stored Tokens
The script reads the stored access and refresh tokens from:

```
/etc/alarm/access.token
/etc/alarm/refresh.token
```

### Step 2: Send Heartbeat to API
A `POST` request is made to the API endpoint `/device/heartbeat/` using the access token.

### Step 3: Check for Token Expiry
If the response indicates that the token has expired:

1. The script attempts to refresh the token by making a `POST` request to `/device/token/refresh/` using the refresh token.
2. If successful, the new access and refresh tokens are stored securely.

### Step 4: Restart Vector with New Token
If new tokens are obtained, Vector is restarted to apply the new credentials.

---

## Troubleshooting
If the heartbeat script fails, check:

```
/var/log/alarm_agent_install.log
```
