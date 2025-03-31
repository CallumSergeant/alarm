This document explains the process that the ALARM agent goes through to generate an access token to communicate with the API.


!!! warning "Important"
    Communication with the API is only authorised when the correct access token is passed along with the request body.

---

##  Secured endpoints
All endpoints that a managed device (a machine with the ALARM agent installed) send data to, require an authorisation bearer token to be sent along with the request body. The following endpoints require a bearer token to communicate with:

- `/logs/`
- `/deregister/`
- `/device/token/refresh/`
- `/device/heartbeat/`

!!! warning "Note"
    It is not intended for a user to directly interact with the API, only the ALARM agent. This is due to the complex token management that has to happen to authenticate with the API. 

---

## Token management
There are 2 tokens issued to a managed device.

| Token         | Expiry   | Stored | Description |
|--------------|--------|----------|-------------|
| Access | 5 mins | /etc/alarm/access.tken | Access token used as bearer token, sent with secure requests to the API |
| Refresh | 24 hours | /etc/alarm/refresh.tken | Refresh token used to get a new set of access and refresh tokens upon access token expiration |

These token are initially aquired when the device first registers with the API. The ALARM heartbeat script runs every 60 seconds to check-in with the device, during this process, if the token it currently holds has expired, it will use its refresh token to request a new set of tokens. It does this by calling `/device/token/refresh/` with the refresh token as the bearer authorisation header.

When the device is deregistered, the tokens are removed from the device.

#### Changing token expirations
The token expiration durations can be altered in the projects global `settings.py` file. This is found in `app/alarm/`. These times can be found under the `SIMPLE_JWT` settings.
