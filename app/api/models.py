from django.db import models
from django.utils.timezone import now
from django.utils import timezone
import uuid

class LogEntry(models.Model):
    timestamp = models.DateTimeField()
    source_ip = models.GenericIPAddressField()
    action = models.CharField(max_length=100)
    source = models.CharField(max_length=50, default='fail2ban')
    host = models.CharField(max_length=255, default='unknown')

class ManagedDevice(models.Model):
    unique_id = models.CharField(max_length=255, unique=True)
    hostname = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    os = models.CharField(max_length=100)
    last_check_in = models.DateTimeField(default=now)
    status = models.CharField(max_length=50, default="Healthy")

    def __str__(self):
        return self.hostname

class InstallToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return str(self.token)

class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='INFO')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.severity}] {self.title}"

class SystemScript(models.Model):
    SCRIPT_CHOICES = [
        ("install", "Install Script"),
        ("uninstall", "Uninstall Script"),
    ]
    
    name = models.CharField(max_length=20, choices=SCRIPT_CHOICES, unique=True)
    content = models.TextField()
    last_updated = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)

class BlockedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True)
    banned_at = models.DateTimeField(default=timezone.now)
    reason = models.TextField(blank=True, null=True)
    currently_banned = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.ip_address} - {'Banned' if self.currently_banned else 'Unbanned'}"