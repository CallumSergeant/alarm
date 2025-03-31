#!/bin/bash

# Variables
API_URL="https://alarm.sgt.me.uk/api"
UNIQUE_ID="$1"
TOKEN_DIR="/etc/alarm"
ACCESS_TOKEN_FILE="${TOKEN_DIR}/access.token"
REFRESH_TOKEN_FILE="${TOKEN_DIR}/refresh.token"
ENV_FILE="/etc/default/vector"
LOG_FILE="/var/log/alarm_agent_install.log"
BLOCKLIST_API="${API_URL}/blocklist/"
JAIL_NAME="sshd"
SYNC_SCRIPT="/usr/local/bin/fail2ban_sync.sh"
HOSTNAME=$(hostname)
OS=$(lsb_release -d | awk -F"\t" '{print $2}')

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Ensure the script is run as root
if [[ $EUID -ne 0 ]]; then
    log "This script must be run as root. Exiting."
    exit 1
fi

log "Starting installation of ALARM agent."

# Create alarm-agent User
log "Creating alarm-agent user..."
if ! id "alarm-agent" &>/dev/null; then
    useradd -r -s /usr/sbin/nologin alarm-agent
    log "User alarm-agent created."
else
    log "User alarm-agent already exists."
fi

# Grant permission to restart Vector
log "Granting alarm-agent permission to restart Vector..."
echo "alarm-agent ALL=NOPASSWD: /bin/systemctl restart vector" | sudo tee -a /etc/sudoers.d/alarm-agent

# Grant permission to manage Fail2Ban
log "Granting alarm-agent permission to manage Fail2Ban..."
echo "alarm-agent ALL=NOPASSWD: /usr/bin/fail2ban-client" | sudo tee -a /etc/sudoers.d/alarm-agent

chmod 440 /etc/sudoers.d/alarm-agent

# Step 1: Get Host IP Address
log "Detecting host IP address..."
HOST_IP=$(hostname -I | awk '{print $1}')
if [[ -z "$HOST_IP" ]]; then
    log "Failed to detect host IP address. Exiting."
    exit 1
fi
log "Detected host IP: $HOST_IP"

# Step 2: Install Fail2Ban
log "Installing Fail2Ban..."
apt-get update -y && apt-get install -y fail2ban
if [[ $? -ne 0 ]]; then
    log "Failed to install Fail2Ban. Exiting."
    exit 1
fi

# Step 3: Install jq
log "Installing jq..."
apt-get install -y jq
if [[ $? -ne 0 ]]; then
    log "Failed to install jq. Exiting."
    exit 1
fi

# Step 4: Install Vector
log "Installing Vector..."
bash -c "$(curl -L https://setup.vector.dev)"
apt-get install -y vector
if [[ $? -ne 0 ]]; then
    log "Failed to install Vector. Exiting."
    exit 1
fi

# Step 5: Register Device with API
log "Registering device with API..."
response=$(curl -s -X POST "${API_URL}/register/" \
  -H "Content-Type: application/json" \
  -d "{
    \"hostname\": \"${HOSTNAME}\",
    \"os\": \"${OS}\",
    \"install_token\": \"${UNIQUE_ID}\" 
  }")

ACCESS_TOKEN=$(echo "$response" | jq -r '.tokens.access')
REFRESH_TOKEN=$(echo "$response" | jq -r '.tokens.refresh')

if [[ -z "$ACCESS_TOKEN" || -z "$REFRESH_TOKEN" ]]; then
    log "Failed to register device. Response: $response"
    exit 1
fi

log "Device registered successfully. Tokens obtained."

# Step 6: Store Tokens Securely
log "Storing tokens securely..."
mkdir -p "${TOKEN_DIR}"
chmod 700 "${TOKEN_DIR}"
echo "$ACCESS_TOKEN" > "${ACCESS_TOKEN_FILE}"
echo "$REFRESH_TOKEN" > "${REFRESH_TOKEN_FILE}"
echo "VECTOR_ACCESS_TOKEN=${ACCESS_TOKEN}" > ${ENV_FILE}
chmod 600 "${ACCESS_TOKEN_FILE}" "${REFRESH_TOKEN_FILE}" "${ENV_FILE}"

# Set correct ownership for alarm-agent
sudo chown -R alarm-agent:alarm-agent /etc/alarm
sudo chmod 640 /etc/alarm/access.token
sudo chmod 640 /etc/alarm/refresh.token
sudo chown alarm-agent:alarm-agent /etc/default/vector
sudo chmod 640 /etc/default/vector


# Step 7: Configure Vector
log "Configuring Vector..."
cat <<EOF > /etc/vector/vector.yaml
sources:
  auth_logs:
    type: file
    include:
      - /var/log/auth.log
      - /var/log/secure
    read_from: beginning
    ignore_older: 3600

transforms:
  filter_login_attempts:
    type: remap
    inputs: ["auth_logs"]
    source: |
      .message = to_string(.message) ?? ""
      if !(contains(.message, "Accepted password") || contains(.message, "Failed password")) {
        abort
      }

sinks:
  django_api:
    type: http
    inputs: ["filter_login_attempts"]
    uri: "${API_URL}/logs/"
    encoding:
      codec: json
    auth:
      strategy: bearer
      token: "\${VECTOR_ACCESS_TOKEN}"
    healthcheck: true
EOF

# Step 8: Enable and Start Vector Service
log "Starting Vector service..."
systemctl enable vector
systemctl restart vector
if [[ $? -ne 0 ]]; then
    log "Failed to start Vector. Exiting."
    exit 1
fi

# Step 9: Create Heartbeat Script
log "Setting up heartbeat script..."

cat <<EOF > /usr/local/bin/heartbeat.sh
#!/bin/bash

ACCESS_TOKEN=\$(cat /etc/alarm/access.token)
REFRESH_TOKEN=\$(cat /etc/alarm/refresh.token)

echo "VECTOR_ACCESS_TOKEN=\$ACCESS_TOKEN" > ${ENV_FILE}

response=\$(curl -s -X POST "${API_URL}/device/heartbeat/" \
  -H "Authorization: Bearer \${ACCESS_TOKEN}" \
  -H "Content-Type: application/json")

if echo "\$response" | grep -q "Token has expired"; then
    echo "Access token expired. Attempting to refresh..."

    refresh_response=\$(curl -s -X POST "${API_URL}/device/token/refresh/" \
      -H "Authorization: Bearer \${REFRESH_TOKEN}" \
      -H "Content-Type: application/json")

    NEW_ACCESS_TOKEN=\$(echo "\$refresh_response" | jq -r '.tokens.access')
    NEW_REFRESH_TOKEN=\$(echo "\$refresh_response" | jq -r '.tokens.refresh')

    if [[ -n "\$NEW_ACCESS_TOKEN" && -n "\$NEW_REFRESH_TOKEN" && "\$NEW_ACCESS_TOKEN" != "null" ]]; then
        echo "\$NEW_ACCESS_TOKEN" > "/etc/alarm/access.token"
        echo "\$NEW_REFRESH_TOKEN" > "/etc/alarm/refresh.token"
        echo "VECTOR_ACCESS_TOKEN=\$NEW_ACCESS_TOKEN" > ${ENV_FILE}
        sudo systemctl restart vector
        echo "Tokens refreshed and Vector restarted."
    else
        echo "Token refresh failed. Response: \$refresh_response"
    fi
else
    echo "Heartbeat sent successfully."
fi
EOF

chmod +x /usr/local/bin/heartbeat.sh

# Step 10: Setup Fail2Ban Sync Script
log "Setting up Fail2Ban sync script..."


cat <<EOF > /usr/local/bin/fail2ban_sync.sh
#!/bin/bash

# API Configuration
BLOCKLIST_API="https://alarm.sgt.me.uk/api/blocklist/"
REPORT_BAN_API="https://alarm.sgt.me.uk/api/report_ban/"
JAIL_NAME="sshd"
ALREADY_REPORTED_FILE="/etc/alarm/already_reported_bans.txt"

# Ensure the reported bans file exists
touch "\$ALREADY_REPORTED_FILE"

# Fetch the latest blocklist from Django API
RESPONSE=\$(curl -s "\$BLOCKLIST_API")

BLOCKLIST=\$(echo "\$RESPONSE" | jq -r '.blocked_ips[]')
UNBLOCKLIST=\$(echo "\$RESPONSE" | jq -r '.unblocked_ips[]')

if [[ -z "\$BLOCKLIST" ]]; then
    echo "No blocked IPs received from API."
fi

# Sync Fail2Ban with the blocklist
for IP in \$BLOCKLIST; do
    if ! sudo fail2ban-client status "\$JAIL_NAME" | grep -q "\$IP"; then
        sudo fail2ban-client set "\$JAIL_NAME" banip "\$IP"
    fi
done

# Unban IPs that should be removed
for IP in \$UNBLOCKLIST; do
    if sudo fail2ban-client status "\$JAIL_NAME" | grep -q "\$IP"; then
        sudo fail2ban-client set "\$JAIL_NAME" unbanip "\$IP"
        echo "Unbanned \$IP as per API instruction."
    fi
done

# Get currently banned IPs from Fail2Ban
CURRENT_BANS=\$(sudo fail2ban-client status "\$JAIL_NAME" | grep "Banned IP list" | cut -d ":" -f2 | tr -s " ")

if [[ -z "\$CURRENT_BANS" ]]; then
    echo "No new bans found in Fail2Ban."
    exit 0
fi

# Iterate over banned IPs and report new ones
for IP in \$CURRENT_BANS; do
    if ! grep -q "\$IP" "\$ALREADY_REPORTED_FILE"; then
        # Report the ban to Django API
        response=\$(curl -s -X POST "\$REPORT_BAN_API" \
            -H "Content-Type: application/json" \
            -d "{\"ip\": \"\$IP\", \"reason\": \"Detected by Fail2Ban\"}")

        if echo "\$response" | grep -q "status"; then
            echo "\$IP" >> "\$ALREADY_REPORTED_FILE"
            echo "Reported \$IP to API."
        else
            echo "Failed to report \$IP. Response: \$response"
        fi
    fi
done
EOF

# Ensure correct permissions
chmod +x /usr/local/bin/fail2ban_sync.sh
chown alarm-agent:alarm-agent /usr/local/bin/fail2ban_sync.sh

log "Fail2Ban sync script created successfully."

# Step 12: Create ALARM Sync Script
log "Setting up ALARM sync script..."

SYNC_ALL_SCRIPT="/usr/local/bin/alarm_sync.sh"

cat << EOF > "${SYNC_ALL_SCRIPT}"
#!/bin/bash

# Run heartbeat first
/usr/local/bin/heartbeat.sh

# Run Fail2Ban sync script
/usr/local/bin/fail2ban_sync.sh
EOF

# Ensure correct permissions
chmod +x "${SYNC_ALL_SCRIPT}"
chown alarm-agent:alarm-agent "${SYNC_ALL_SCRIPT}"

log "ALARM sync script created successfully."

# Step 13: Add Single Cron Job for ALARM Sync
log "Setting up cron job for ALARM sync..."
(crontab -l 2>/dev/null | grep -v "heartbeat.sh" | grep -v "fail2ban_sync.sh"; echo "*/1 * * * * /bin/bash ${SYNC_ALL_SCRIPT}") | sort -u | sudo -u alarm-agent crontab -

# Step 14: Configure Fail2Ban to ban after 5 failed login attempts
log "Configuring Fail2Ban for SSH brute-force protection..."

JAIL_CONFIG="/etc/fail2ban/jail.local"

# Ensure jail.local exists
touch "$JAIL_CONFIG"

cat << EOF > "$JAIL_CONFIG"
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
findtime = 600
bantime = 1
EOF

log "Fail2Ban SSH jail configured successfully."

# Restart Fail2Ban to apply changes
systemctl restart fail2ban
if [[ $? -ne 0 ]]; then
    log "Failed to restart Fail2Ban. Exiting."
    exit 1
fi

log "Fail2Ban restarted successfully with new jail settings."


log "Installation completed successfully."
