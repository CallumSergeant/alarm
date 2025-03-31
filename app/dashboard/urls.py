from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard-home'),
    path('login-attempts/', views.login_attempt_list, name='login-attempt-list'),
    path('blocked-ips/', views.blocked_ips, name='blocked-ips'),
    path("toggle_ban_ip/<str:ip_address>/", views.toggle_ban_ip, name="toggle-ban-ip"),
    path('alerts/', views.alerts_view, name='alerts'),
    path('settings/', views.system_settings, name='system-settings'),
    path('managed-devices/', views.managed_devices, name='managed-devices'),
    path('generate-install-command/', views.generate_install_command, name='generate-install-command'),
]
