from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.utils.timezone import now
from django.http import JsonResponse
import re
import uuid

from .models import LogEntry, ManagedDevice, InstallToken, BlockedIP
from .utils import (
    generate_device_tokens,
    verify_token,
    get_client_ip,
    log_alert,
    detect_distributed_attack
)


class LogView(APIView):

    def post(self, request):
        """Handles log submissions from managed devices."""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            log_alert("Log Submission Failed", "Authorization header with Bearer token is required.", severity='ERROR')
            return Response({"error": "Authorization header with Bearer token is required."}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = auth_header.split(' ')[1]
        try:
            decoded_token = verify_token(access_token, token_type='access')
            unique_id = decoded_token.get('unique_id')
            device = ManagedDevice.objects.get(unique_id=unique_id)
            log_alert("Authorization Successful", f"Device {device.hostname} authorized for log submission.", severity='INFO')
        except ManagedDevice.DoesNotExist:
            log_alert("Authorization Failed", "Device not found.", severity='WARNING')
            return Response({"error": "Device not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_alert("Authorization Error", str(e), severity='ERROR')
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        log_data = request.data
        logs = log_data if isinstance(log_data, list) else [log_data]

        for entry in logs:
            client_ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META.get('REMOTE_ADDR')
            message = entry.get('message')
            timestamp = entry.get('timestamp')
            host = entry.get('host', client_ip)

            if not message or not timestamp:
                log_alert("Invalid Log Data", "Missing 'message' or 'timestamp' in log data.", severity='ERROR')
                return Response({"error": "Missing 'message' or 'timestamp' in log data."}, status=status.HTTP_400_BAD_REQUEST)

            ip_match = re.search(r'from (\d{1,3}(?:\.\d{1,3}){3})', message)
            source_ip = ip_match.group(1) if ip_match else None

            action = "Accepted password" if "Accepted password" in message else ("Failed password" if "Failed password" in message else "Unknown")

            if not source_ip:
                log_alert("Invalid Log Data", "Source IP not found in log message.", severity='ERROR')
                return Response({"error": "Source IP not found in log message."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                LogEntry.objects.create(
                    timestamp=timestamp,
                    source_ip=source_ip,
                    action=action,
                    source="vector",
                    host=host
                )
                log_alert("Log Entry Created", f"Log entry created for source IP {source_ip}.", severity='INFO')
            except Exception as e:
                log_alert("Log Creation Failed", str(e), severity='ERROR')
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        detect_distributed_attack()
        return Response({"status": "Log entries created"}, status=status.HTTP_201_CREATED)


class RegisterDeviceView(APIView):
    def post(self, request):
        """Registers a new managed device with valid install token."""
        data = request.data
        log_alert("Device Registration Attempt", "Attempt to register a new device.", severity='INFO')

        hostname = data.get('hostname')
        os = data.get('os')
        install_token = data.get('install_token')

        if not hostname or not os or not install_token:
            log_alert("Device Registration Failed", "Hostname, OS, and install token are required.", severity='ERROR')
            return Response({"error": "Hostname, OS, and install token are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_entry = InstallToken.objects.filter(token=install_token, is_used=False).first()

            if not token_entry or token_entry.is_expired():
                log_alert("Invalid Install Token", "Invalid or expired token provided.", severity='WARNING')
                return Response({"error": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

            token_entry.is_used = True
            token_entry.save()

            unique_id = str(uuid.uuid4())
            client_ip = get_client_ip(request)

            device, _ = ManagedDevice.objects.update_or_create(
                unique_id=unique_id,
                defaults={
                    'hostname': hostname,
                    'ip_address': client_ip,
                    'os': os,
                    'last_check_in': now(),
                    'status': 'Healthy',
                }
            )

            tokens = generate_device_tokens(device.unique_id)
            log_alert("Device Registered", f"Device {hostname} registered successfully.", severity='INFO')

            return Response({
                "message": "Device registered successfully.",
                "unique_id": str(device.unique_id),
                "tokens": tokens
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            log_alert("Device Registration Failed", str(e), severity='ERROR')
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeregisterDeviceView(APIView):
    def delete(self, request):
        """Deregisters a managed device using a valid token."""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            log_alert("Deregistration Failed", "Authorization header missing or improperly formatted.", severity='ERROR')
            return Response({"detail": "Authorization header missing or improperly formatted."}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = auth_header.split(' ')[1]
        try:
            decoded_token = verify_token(access_token, token_type='access')
            unique_id = decoded_token.get('unique_id')
            device = ManagedDevice.objects.get(unique_id=unique_id)
            device.delete()
            log_alert("Device Deregistered", f"Device {device.hostname} deregistered successfully.", severity='INFO')
            return Response({"detail": "Device deregistered successfully."}, status=status.HTTP_200_OK)
        except ManagedDevice.DoesNotExist:
            log_alert("Deregistration Failed", "Device not found.", severity='WARNING')
            return Response({"detail": "Device not found or already deregistered."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_alert("Deregistration Error", str(e), severity='ERROR')
            return Response({"detail": f"Error during deregistration: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


class RefreshDeviceTokenView(APIView):
    def post(self, request):
        """Refreshes access and refresh tokens for an authenticated device."""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            log_alert("Token Refresh Failed", "Authorization header with Bearer token is required.", severity='ERROR')
            return Response({"error": "Authorization header with Bearer token is required."}, status=status.HTTP_401_UNAUTHORIZED)

        refresh_token = auth_header.split(' ')[1]
        try:
            decoded_token = verify_token(refresh_token, token_type='refresh')
            unique_id = decoded_token.get('unique_id')

            device = ManagedDevice.objects.get(unique_id=unique_id)
            tokens = generate_device_tokens(device.unique_id)

            log_alert("Token Refreshed", f"Tokens refreshed for device {device.hostname}.", severity='INFO')
            return Response({"message": "Tokens refreshed successfully.", "tokens": tokens}, status=status.HTTP_200_OK)
        except ManagedDevice.DoesNotExist:
            log_alert("Token Refresh Failed", "Device not found.", severity='WARNING')
            return Response({"error": "Device not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_alert("Token Refresh Error", str(e), severity='ERROR')
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeviceHeartbeatView(APIView):
    def post(self, request):
        """Receives heartbeat from a device and updates its check-in time."""
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            log_alert("Heartbeat Failed", "Authorization token missing.", severity='ERROR')
            return Response({"error": "Authorization token missing."}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = auth_header.split(' ')[1]
        try:
            decoded_token = verify_token(access_token, token_type='access')
            unique_id = decoded_token.get('unique_id')

            device = ManagedDevice.objects.get(unique_id=unique_id)
            device.last_check_in = now()
            device.save()

            log_alert("Heartbeat Received", f"Heartbeat received from device {device.hostname}.", severity='INFO')
            return Response({"message": "Heartbeat received."}, status=status.HTTP_200_OK)
        except ManagedDevice.DoesNotExist:
            log_alert("Heartbeat Failed", "Device not found.", severity='WARNING')
            return Response({"error": "Device not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            log_alert("Heartbeat Error", str(e), severity='ERROR')
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DeviceStatusView(APIView):
    def get(self, request, token):
        """Returns install status for a device given a token."""
        try:
            device_token = InstallToken.objects.get(token=token)

            if device_token.is_used:
                log_alert("Device Status Check", f"Device with token {token} is healthy.", severity='INFO')
                return Response({"status": "Healthy"}, status=status.HTTP_200_OK)
            else:
                log_alert("Device Status Check", f"Device with token {token} is pending.", severity='INFO')
                return Response({"status": "Pending"}, status=status.HTTP_200_OK)
        except InstallToken.DoesNotExist:
            log_alert("Device Status Check Failed", f"Device with token {token} not found.", severity='WARNING')
            return Response({"error": "Device not found"}, status=status.HTTP_404_NOT_FOUND)


class GetBlocklistView(APIView):
    def get(self, request):
        """Returns blocked and unblocked IP addresses."""
        try:
            blocked_ips = BlockedIP.objects.filter(currently_banned=True).values_list("ip_address", flat=True)
            unblocked_ips = BlockedIP.objects.filter(currently_banned=False).values_list("ip_address", flat=True)
            return Response({"blocked_ips": list(blocked_ips), "unblocked_ips": list(unblocked_ips)}, status=status.HTTP_200_OK)
        except Exception as e:
            log_alert("Error getting blocklist", f"{str(e)}", severity='ERROR')
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReportBanView(APIView):
    def post(self, request):
        """Receives a report of a newly banned IP from a device."""
        try:
            data = request.data
            ip = data.get("ip")
            reason = data.get("reason", "No reason provided")

            if not ip:
                log_alert("Error blocking IP", "IP address is required", severity='WARNING')
                return Response({"error": "IP address is required"}, status=status.HTTP_400_BAD_REQUEST)

            blocked_ip, _ = BlockedIP.objects.get_or_create(ip_address=ip, defaults={"reason": reason})

            if not blocked_ip.currently_banned:
                blocked_ip.currently_banned = True
                blocked_ip.banned_at = now()
                blocked_ip.save()

            log_alert("IP Blocked", f"{blocked_ip} has been blocked.")
            return Response({"status": "IP added to blocklist"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            log_alert("Error blocking IP", f"{str(e)}", severity='ERROR')
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
