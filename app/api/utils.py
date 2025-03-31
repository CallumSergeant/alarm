import jwt
from django.conf import settings
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.db.models import Count

from .models import Alert, BlockedIP, LogEntry

# Token lifetimes
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)

def generate_device_tokens(unique_id):
    """
    Generates access and refresh JWT tokens for a given device unique ID.
    """
    access_payload = {
        'unique_id': str(unique_id),
        'exp': datetime.utcnow() + ACCESS_TOKEN_LIFETIME,
        'type': 'access'
    }

    refresh_payload = {
        'unique_id': str(unique_id),
        'exp': datetime.utcnow() + REFRESH_TOKEN_LIFETIME,
        'type': 'refresh'
    }

    access_token = jwt.encode(access_payload, settings.SECRET_KEY, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, settings.SECRET_KEY, algorithm='HS256')

    return {
        "access": access_token,
        "refresh": refresh_token
    }

def verify_token(token, token_type='access'):
    """
    Verifies and decodes a JWT token and ensures the type matches.

    Raises jwt.InvalidTokenError if invalid or expired.
    """
    try:
        decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        if decoded.get('type') != token_type:
            raise jwt.InvalidTokenError("Invalid token type.")
        return decoded
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token has expired.")
    except jwt.InvalidTokenError as e:
        raise jwt.InvalidTokenError(str(e))

def get_client_ip(request):
    """
    Extracts the client IP address from the request headers.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def log_alert(title, message, severity='INFO'):
    """
    Logs an alert to the Alert model.

    :param title: Short title of the alert
    :param message: Detailed alert message
    :param severity: Severity level ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    Alert.objects.create(title=title, message=message, severity=severity)

def detect_distributed_attack():
    """
    Detects brute-force attacks by identifying IPs with multiple failed login attempts within 1 minute.
    Automatically re-bans IPs if needed.
    """
    time_threshold = now() - timedelta(minutes=1)

    suspicious_ips = (
        LogEntry.objects.filter(action="Failed password", timestamp__gte=time_threshold)
        .values("source_ip")
        .annotate(attempt_count=Count("id"))
        .filter(attempt_count__gte=5)
    )

    for entry in suspicious_ips:
        ip = entry["source_ip"]
        blocked_ip, created = BlockedIP.objects.get_or_create(
            ip_address=ip,
            defaults={"reason": "Distributed brute-force attack", "currently_banned": True}
        )

        if not created and not blocked_ip.currently_banned:
            blocked_ip.currently_banned = True
            blocked_ip.banned_at = now()
            blocked_ip.save()
            log_alert("Global Ban", f"Global Re-Ban Issued: {ip}")
