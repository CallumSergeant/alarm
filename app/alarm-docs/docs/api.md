# ALARM API Documentation

Welcome to the ALARM API documentation. This API enables managed devices to report login attempts, register, deregister, refresh tokens, send heartbeats, and manage blocked IPs.

## Base URL
```
https://alarm.sgt.me.uk/api/
```

---

##  Log Submission Endpoint
### **POST /log/**
**Description:** Accepts log entries from a managed device.

#### **Request Headers:**
| Header         | Type   | Required | Description |
|--------------|--------|----------|-------------|
| Authorization | Bearer Token | ✅ | Access token for authentication |

#### **Request Body (JSON):**
```json
{
    "message": "Failed password for root from 192.168.1.1",
    "timestamp": "2025-02-12T10:00:00Z",
    "host": "server-01"
}
```

#### **Response (Success - 201 Created):**
```json
{
    "status": "Log entries created"
}
```
#### **Response (Error - 400 Bad Request):**
```json
{
    "error": "Missing 'message' or 'timestamp' in log data."
}
```

---

##  Register a New Device
### **POST /register-device/**
**Description:** Registers a new managed device using an installation token.

#### **Request Body (JSON):**
```json
{
    "hostname": "device-01",
    "os": "Ubuntu 22.04",
    "install_token": "abcd1234"
}
```

#### **Response (Success - 201 Created):**
```json
{
    "message": "Device registered successfully.",
    "unique_id": "123e4567-e89b-12d3-a456-426614174000",
    "tokens": { "access": "token123", "refresh": "token456" }
}
```

#### **Response (Error - 400 Bad Request):**
```json
{
    "error": "Invalid or expired token."
}
```

---

##  Deregister a Device
### **DELETE /deregister-device/**
**Description:** Removes a registered device from the system.

#### **Request Headers:**
| Header         | Type   | Required | Description |
|--------------|--------|----------|-------------|
| Authorization | Bearer Token | ✅ | Access token for authentication |

#### **Response (Success - 200 OK):**
```json
{
    "detail": "Device deregistered successfully."
}
```

#### **Response (Error - 404 Not Found):**
```json
{
    "detail": "Device not found or already deregistered."
}
```

---

##  Refresh Device Token
### **POST /refresh-token/**
**Description:** Refreshes an access token for a registered device.

#### **Request Headers:**
| Header         | Type   | Required | Description |
|--------------|--------|----------|-------------|
| Authorization | Bearer Token | ✅ | Refresh token for authentication |

#### **Response (Success - 200 OK):**
```json
{
    "message": "Tokens refreshed successfully.",
    "tokens": { "access": "new_access_token", "refresh": "new_refresh_token" }
}
```

#### **Response (Error - 401 Unauthorized):**
```json
{
    "error": "Device not found."
}
```

---

##  Send Device Heartbeat
### **POST /heartbeat/**
**Description:** Updates the last check-in time of a registered device.

#### **Request Headers:**
| Header         | Type   | Required | Description |
|--------------|--------|----------|-------------|
| Authorization | Bearer Token | ✅ | Access token for authentication |

#### **Response (Success - 200 OK):**
```json
{
    "message": "Heartbeat received."
}
```

---

##  Get Device Status
### **GET /device-status/{token}/**
**Description:** Retrieves the registration status of a device.

#### **Response (Success - 200 OK):**
```json
{
    "status": "Healthy"
}
```
#### **Response (Error - 404 Not Found):**
```json
{
    "error": "Device not found."
}
```

---

##  Get Blocked IP List
### **GET /get-blocklist/**
**Description:** Retrieves the list of blocked and unblocked IPs.

#### **Response (Success - 200 OK):**
```json
{
    "blocked_ips": ["192.168.1.1", "10.0.0.5"],
    "unblocked_ips": ["172.16.0.2"]
}
```

---

##  Report a New Banned IP
### **POST /report-ban/**
**Description:** Receives a newly banned IP from a managed device.

#### **Request Body (JSON):**
```json
{
    "ip": "192.168.1.100",
    "reason": "Too many failed SSH login attempts"
}
```

#### **Response (Success - 201 Created):**
```json
{
    "status": "IP added to blocklist"
}
```
#### **Response (Error - 400 Bad Request):**
```json
{
    "error": "IP address is required."
}
```

---

##  Notes
- **Authentication:** Most endpoints require a **Bearer token** for authentication.
- **Timestamps:** Follow the format `YYYY-MM-DDTHH:MM:SSZ`.
- **Error Handling:** All errors return standard HTTP status codes with JSON error messages.
