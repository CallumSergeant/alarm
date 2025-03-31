from django.urls import path
from .views import (
    LogView,
    RegisterDeviceView,
    RefreshDeviceTokenView,
    DeregisterDeviceView,
    DeviceHeartbeatView,
    DeviceStatusView,
    GetBlocklistView,
    ReportBanView,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('logs/', LogView.as_view(), name='logs'),
    path('register/', RegisterDeviceView.as_view(), name='register'),
    path('deregister/', DeregisterDeviceView.as_view(), name='deregister'),
    path('device/token/refresh/', RefreshDeviceTokenView.as_view(), name='refresh_device_token'),
    path('device/heartbeat/', DeviceHeartbeatView.as_view(), name='device_heartbeat'),
    path('device/status/<str:token>/', DeviceStatusView.as_view(), name='device_status'),
    path("report_ban/", ReportBanView.as_view(), name="report_ban"),
    path("blocklist/", GetBlocklistView.as_view(), name="get_blocklist"),
]