from locust import HttpUser, task, between
import json
import datetime

class AlarmAPITest(HttpUser):
    """
    Locust load test user that simulates registering a device and submitting logs to the ALARM API.
    """
    wait_time = between(1, 3)

    def on_start(self):
        """Runs once per Locust user when they start."""
        if not hasattr(self.environment, "access_token"):
            self.environment.access_token = self.get_token()

    def get_token(self):
        """Register a device and retrieve a valid access token."""
        install_token = "9ac719da-57fb-4cdc-b839-a623cffc226b"

        register_payload = {
            "hostname": "locust-test-device",
            "os": "Ubuntu",
            "install_token": install_token
        }

        response = self.client.post(
            "https://alarm.sgt.me.uk/api/register/",
            json=register_payload
        )

        if response.status_code == 201:
            tokens = response.json().get("tokens")
            return tokens.get("access")
        else:
            print(f"Failed to get access token! Response: {response.text}")
            return None

    @task
    def submit_log(self):
        """Simulate a log submission to the LogView endpoint."""
        if not hasattr(self.environment, "access_token"):
            print("Skipping log submission: No valid token")
            return

        headers = {
            "Authorization": f"Bearer {self.environment.access_token}"
        }

        log_data = [
            {
                "message": "Failed password for invalid user admin from 192.168.1.200",
                "timestamp": datetime.datetime.utcnow().isoformat(),
                "host": "simulated-device"
            }
        ]

        response = self.client.post(
            "https://alarm.sgt.me.uk/api/logs/",
            json=log_data,
            headers=headers
        )

        if response.status_code == 400:
            print("Token expired, fetching new one...")
            self.environment.access_token = self.get_token()
        elif response.status_code == 201:
            print("Log submitted successfully.")
        else:
            print(f"Log submission failed: {response.status_code}, Response: {response.text}")