from django.contrib import admin
from .models import LogEntry, ManagedDevice, InstallToken, Alert, SystemScript, BlockedIP

admin.site.register(LogEntry)
admin.site.register(ManagedDevice)
admin.site.register(InstallToken)
admin.site.register(Alert)
admin.site.register(SystemScript)
admin.site.register(BlockedIP)