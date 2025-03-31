from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils.timezone import now, timedelta
from datetime import datetime
import uuid
import jwt
from django.conf import settings

from .models import ManagedDevice, InstallToken, BlockedIP, Alert, LogEntry
from .utils import generate_device_tokens, verify_token


class AlarmAPITests(TestCase):
    def setUp(self):
        """Set up common test data for API tests."""
        self.client = APIClient()

        self.install_token = InstallToken.objects.create(
            token="497dcba3-ecbf-4587-a2dd-5eb0665e6880",
            is_used=False,
            expires_at=now() + timedelta(days=7)
        )

        self.device_uuid = str(uuid.uuid4())
        self.device = ManagedDevice.objects.create(
            unique_id=self.device_uuid,
            hostname="test-device",
            ip_address="192.168.1.100",
            os="Linux",
            last_check_in=now(),
            status="Healthy"
        )

        self.tokens = generate_device_tokens(self.device.unique_id)
        self.access_token = self.tokens["access"]
        self.refresh_token = self.tokens["refresh"]

        expired_payload = {
            'unique_id': str(self.device.unique_id),
            'exp': now() - timedelta(minutes=1),
            'type': 'access'
        }
        self.expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm='HS256')

        self.invalid_token = "497dcba3-ecbf-4587-a2dd-5eb0665e6880"

    def test_register_device(self):
        """Test registering a device with a valid install token."""
        response = self.client.post("/api/register/", {
            "hostname": "new-device",
            "os": "Ubuntu",
            "install_token": self.install_token.token
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)

    def test_register_device_missing_fields(self):
        """Test registering a device with missing required fields."""
        response = self.client.post("/api/register/", {
            "hostname": "new-device",
            "os": ""
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_log_submission_with_auth(self):
        """Test submitting logs with valid authentication."""
        log_data = {
            "message": "Failed password for invalid user admin from 192.168.1.200",
            "timestamp": now().isoformat(),
            "host": "test-device"
        }
        response = self.client.post(
            "/api/logs/",
            log_data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthorized_log_submission(self):
        """Test submitting logs without authentication."""
        response = self.client.post("/api/logs/", {"message": "Test log"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token_handling(self):
        """Test API response when using an expired token."""
        response = self.client.post(
            "/api/logs/",
            {"message": "Test log", "timestamp": now().isoformat()},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.expired_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_log_submission(self):
        """Test submitting logs with missing message or timestamp."""
        log_data = {
            "message": "",
            "timestamp": now().isoformat(),
            "host": "test-device"
        }
        response = self.client.post(
            "/api/logs/",
            log_data,
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deregister_device(self):
        """Test deregistering a device with a valid access token."""
        response = self.client.delete(
            "/api/deregister/",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_deregister_device_invalid_token(self):
        """Test deregistering a device with an invalid token."""
        response = self.client.delete(
            "/api/deregister/",
            HTTP_AUTHORIZATION=f"Bearer {self.invalid_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_heartbeat_checkin(self):
        """Test device heartbeat check-in."""
        response = self.client.post(
            "/api/device/heartbeat/",
            {},
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_device_status_check(self):
        """Test checking device status with a valid token."""
        response = self.client.get(f"/api/device/status/{self.install_token.token}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_device_status_check_invalid(self):
        """Test checking device status with an invalid token."""
        response = self.client.get("/api/device/status/4c8f6d82-e4c6-4478-92eb-d9342500f006/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_refresh_token(self):
        """Test refreshing access tokens using a valid refresh token."""
        response = self.client.post(
            "/api/device/token/refresh/",
            {},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.refresh_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)

    def test_invalid_refresh_token(self):
        """Test attempting to refresh with an invalid token."""
        response = self.client.post(
            "/api/device/token/refresh/",
            {},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.invalid_token}"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_blocklist(self):
        """Test retrieving the blocklist."""
        BlockedIP.objects.create(ip_address="192.168.1.200", currently_banned=True)
        response = self.client.get("/api/blocklist/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("blocked_ips", response.data)

    def test_report_ban(self):
        """Test reporting an IP to the blocklist."""
        response = self.client.post(
            "/api/report_ban/",
            {"ip": "192.168.1.201", "reason": "Suspicious activity"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(BlockedIP.objects.filter(ip_address="192.168.1.201").exists())

    def test_report_ban_missing_ip(self):
        """Test reporting a ban without an IP address."""
        response = self.client.post("/api/report_ban/", {"reason": "Malicious activity"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AlarmUtilsTestCase(TestCase):
    def setUp(self):
        """Prepare data for utils tests."""
        self.unique_id = "test-device-id"
        self.secret_key = settings.SECRET_KEY

    def test_generate_device_tokens_returns_both_tokens(self):
        tokens = generate_device_tokens(self.unique_id)
        self.assertIn("access", tokens)
        self.assertIn("refresh", tokens)

    def test_generate_device_tokens_access_payload(self):
        tokens = generate_device_tokens(self.unique_id)
        decoded_access = jwt.decode(tokens["access"], self.secret_key, algorithms=['HS256'])
        self.assertEqual(decoded_access["unique_id"], self.unique_id)
        self.assertEqual(decoded_access["type"], "access")
        self.assertIn("exp", decoded_access)

    def test_generate_device_tokens_refresh_payload(self):
        tokens = generate_device_tokens(self.unique_id)
        decoded_refresh = jwt.decode(tokens["refresh"], self.secret_key, algorithms=['HS256'])
        self.assertEqual(decoded_refresh["unique_id"], self.unique_id)
        self.assertEqual(decoded_refresh["type"], "refresh")
        self.assertIn("exp", decoded_refresh)

    def test_verify_token_valid_access(self):
        """Should decode successfully for a valid access token."""
        tokens = generate_device_tokens(self.unique_id)
        decoded = verify_token(tokens["access"], token_type="access")
        self.assertEqual(decoded["unique_id"], self.unique_id)
        self.assertEqual(decoded["type"], "access")

    def test_verify_token_invalid_type(self):
        """Should raise an error if token type doesn't match."""
        tokens = generate_device_tokens(self.unique_id)
        with self.assertRaises(jwt.InvalidTokenError) as cm:
            verify_token(tokens["access"], token_type="refresh")
        self.assertIn("Invalid token type", str(cm.exception))

    def test_verify_token_expired(self):
        """Should raise an error if the token is expired."""
        expired_payload = {
            "unique_id": self.unique_id,
            "exp": datetime.utcnow() - timedelta(seconds=1),
            "type": "access"
        }
        expired_token = jwt.encode(expired_payload, self.secret_key, algorithm='HS256')
        with self.assertRaises(jwt.InvalidTokenError) as cm:
            verify_token(expired_token, token_type="access")
        self.assertIn("Token has expired", str(cm.exception))
