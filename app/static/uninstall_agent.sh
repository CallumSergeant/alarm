#!/bin/bash

# Variables
API_URL="https://alarm.sgt.me.uk/api"
TOKEN_DIR="/etc/alarm"
ACCESS_TOKEN_FILE="${TOKEN_DIR}/access.token"
REFRESH_TOKEN_FILE="${TOKEN_DIR}/refresh.token"
ENV_FILE="/etc/default/vector"
LOG_FILE="/var/log/alarm_agent_uninstall.log"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Ensure the script is run as root
if [[ $EUID -ne 0 ]]; then
    log "This script must be run as root. Exiting."
    exit 1
fi

log "Starting uninstallation of ALARM agent."

# Step 1: Stop and Disable Vector Service
log "Stopping and disabling Vector service..."
systemctl stop vector
systemctl disable vector

# Step 2: Remove Vector
log "Removing Vector..."
apt-get remove --purge -y vector
apt-get autoremove -y

# Step 3: Remove Fail2Ban
log "Removing Fail2Ban..."
apt-get remove --purge -y fail2ban
apt-get autoremove -y

# Step 4: Remove jq
log "Removing jq..."
apt-get remove --purge -y jq
apt-get autoremove -y

# Step 5: Deregister Device from API
if [[ -f "$ACCESS_TOKEN_FILE" ]]; then
    ACCESS_TOKEN=$(cat "$ACCESS_TOKEN_FILE")
    log "Deregistering device from API..."
    curl -s -X DELETE "${API_URL}/deregister/" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}"
else
    log "No access token found. Skipping device deregistration."
fi

# Step 6: Remove Vector Configuration
log "Removing Vector configuration..."
rm -f /etc/vector/vector.yaml

# Step 7: Remove Tokens and Environment File
log "Removing stored tokens and environment file..."
rm -rf "$TOKEN_DIR"
rm -f "$ENV_FILE"

# Step 8: Remove heartbeat script
log "Removing heartbeat script..."
rm -f /usr/local/bin/heartbeat.sh

# Step 9: Remove heartbeat cron job
log "Removing heartbeat cron job..."
crontab -u alarm-agent -l | grep -v "/usr/local/bin/heartbeat.sh" | crontab -u alarm-agent -

# Step 10: Remove sudoers entry
log "Removing sudoers entry for alarm-agent..."
rm -f /etc/sudoers.d/alarm-agent

# Step 11: Remove alarm-agent user
log "Removing alarm-agent user..."
userdel -r alarm-agent

# Step 12: Clean up logs
log "Removing installation log..."
rm -f /var/log/alarm_agent_install.log

log "ALARM agent uninstallation completed successfully."
