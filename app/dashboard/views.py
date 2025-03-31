from datetime import datetime, timedelta
import uuid
import re

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q, Count, F
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.contrib import messages

from api.models import LogEntry, ManagedDevice, InstallToken, Alert, SystemScript, BlockedIP
from api.utils import log_alert

IP_REGEX = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"


def get_failed_logins_count(start_time=None, end_time=None):
    """Returns count of failed logins within an optional time range."""
    query = LogEntry.objects.filter(action='Failed password')
    if start_time:
        query = query.filter(timestamp__gte=start_time)
    if end_time:
        query = query.filter(timestamp__lt=end_time)
    return query.count()


def get_failed_logins_by_hour(last_24_hours):
    """Returns hourly distribution of failed logins in the past 24 hours."""
    failed_logins_data = (
        LogEntry.objects.filter(action='Failed password', timestamp__gte=last_24_hours)
        .annotate(hour=F('timestamp__hour'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )
    all_hours = {hour: 0 for hour in range(24)}
    for entry in failed_logins_data:
        all_hours[entry['hour']] = entry['count']
    return all_hours


def get_successful_logins_count(start_time=None, end_time=None):
    """Returns count of successful logins within an optional time range."""
    query = LogEntry.objects.filter(action='Accepted password')
    if start_time:
        query = query.filter(timestamp__gte=start_time)
    if end_time:
        query = query.filter(timestamp__lt=end_time)
    return query.count()


def get_successful_logins_by_hour(last_24_hours):
    """Returns hourly distribution of successful logins in the past 24 hours."""
    successful_logins_data = (
        LogEntry.objects.filter(action='Accepted password', timestamp__gte=last_24_hours)
        .annotate(hour=F('timestamp__hour'))
        .values('hour')
        .annotate(count=Count('id'))
        .order_by('hour')
    )
    all_hours = {hour: 0 for hour in range(24)}
    for entry in successful_logins_data:
        all_hours[entry['hour']] = entry['count']
    return all_hours


def get_top_failed_logins(start_time, end_time, limit=5):
    """Returns top sources of failed logins in a given time range."""
    return LogEntry.objects.filter(
        action='Failed password', timestamp__gte=start_time, timestamp__lt=end_time
    ).values('host', 'source_ip').annotate(count=Count('id')).order_by('-count')[:limit]


def get_top_successful_logins(start_time, end_time, limit=5):
    """Returns top sources of successful logins in a given time range."""
    return LogEntry.objects.filter(
        action='Accepted password', timestamp__gte=start_time, timestamp__lt=end_time
    ).values('host', 'source_ip').annotate(count=Count('id')).order_by('-count')[:limit]


def prepare_combined_chart_data(failed_data, successful_data):
    """Returns labels and values for login trend chart."""
    labels = [f"{hour:02d}:00" for hour in sorted(failed_data.keys())]
    failed = [failed_data[hour] for hour in sorted(failed_data.keys())]
    successful = [successful_data.get(hour, 0) for hour in sorted(failed_data.keys())]
    return labels, failed, successful


def generate_insights(failed_logins_data, last_24_hours):
    """Generates insights based on failed login data."""
    insights = []
    most_active_hour = max(failed_logins_data, key=failed_logins_data.get)
    most_active_count = failed_logins_data[most_active_hour]

    if most_active_count > 10:
        insights.append(f"Unusual activity detected: {most_active_count} failed logins at {most_active_hour:02d}:00.")

    top_ip = (
        LogEntry.objects.filter(action='Failed password', timestamp__gte=last_24_hours)
        .values('source_ip')
        .annotate(count=Count('id'))
        .order_by('-count')
        .first()
    )
    if top_ip and top_ip['count'] > 1:
        insights.append(f"Suspicious activity: IP {top_ip['source_ip']} attempted {top_ip['count']} failed logins.")

    total_failed_logins = sum(failed_logins_data.values())
    if total_failed_logins == 0:
        insights.append("No failed login attempts detected in the last 24 hours. All clear!")

    average_failed_logins = total_failed_logins / 24
    if most_active_count > average_failed_logins * 2:
        insights.append(f"Spike detected: Failed logins at {most_active_hour:02d}:00 were over double the daily average.")

    return insights


def dashboard_home(request):
    """Renders the main dashboard view with login stats and trends."""
    current_time = timezone.now()
    last_24_hours = current_time - timedelta(hours=24)
    yesterday_24_hours = current_time - timedelta(hours=48)
    last_7_days = current_time - timedelta(days=7)

    failed_logins_count = get_failed_logins_count(last_24_hours)
    yesterday_failed = get_failed_logins_count(yesterday_24_hours, last_24_hours)
    weekly_failed = get_failed_logins_count(last_7_days)
    all_time_failed = get_failed_logins_count()
    failed_diff = failed_logins_count - yesterday_failed

    successful_logins_count = get_successful_logins_count(last_24_hours)
    yesterday_successful = get_successful_logins_count(yesterday_24_hours, last_24_hours)
    weekly_successful = get_successful_logins_count(last_7_days)
    all_time_successful = get_successful_logins_count()
    successful_diff = successful_logins_count - yesterday_successful

    failed_hourly_data = get_failed_logins_by_hour(last_24_hours)
    successful_hourly_data = get_successful_logins_by_hour(last_24_hours)

    top_failed = get_top_failed_logins(last_7_days, current_time)
    top_successful = get_top_successful_logins(last_7_days, current_time)

    labels, failed_data, successful_data = prepare_combined_chart_data(failed_hourly_data, successful_hourly_data)
    insights = generate_insights(failed_hourly_data, last_24_hours)

    context = {
        'labels': labels,
        'failed_data': failed_data,
        'successful_data': successful_data,
        'failed_logins_count': failed_logins_count,
        'failed_difference': failed_diff,
        'failed_abs_difference': abs(failed_diff),
        'weekly_failed_logins_count': weekly_failed,
        'all_time_failed_logins_count': all_time_failed,
        'successful_logins_count': successful_logins_count,
        'successful_difference': successful_diff,
        'successful_abs_difference': abs(successful_diff),
        'weekly_successful_logins_count': weekly_successful,
        'all_time_successful_logins_count': all_time_successful,
        'top_failed_logins': top_failed,
        'top_successful_logins': top_successful,
        'insights': insights,
    }
    return render(request, 'dashboard/dashboard_home.html', context)


def login_attempt_list(request):
    """Displays paginated login attempt list with filters and search."""
    query = request.GET.get('q')
    start_datetime = request.GET.get('start_datetime')
    end_datetime = request.GET.get('end_datetime')
    action_filter = request.GET.get('action')

    log_entries = LogEntry.objects.all()

    if query:
        log_entries = log_entries.filter(
            Q(source_ip__icontains=query) |
            Q(action__icontains=query) |
            Q(host__icontains=query) |
            Q(source__icontains=query)
        )

    if action_filter and action_filter != 'ALL':
        log_entries = log_entries.filter(action=action_filter)

    if start_datetime:
        dt = timezone.make_aware(datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M'))
        log_entries = log_entries.filter(timestamp__gte=dt)

    if end_datetime:
        dt = timezone.make_aware(datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M'))
        log_entries = log_entries.filter(timestamp__lte=dt)

    paginator = Paginator(log_entries.order_by('-timestamp'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/login_attempt_list.html', {
        'page_obj': page_obj,
        'query': query,
        'action_filter': action_filter,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
    })


def blocked_ips(request):
    """Manages and displays blocked IPs with filtering."""
    query = request.GET.get("q", "")
    start_datetime = request.GET.get("start_datetime", "")
    end_datetime = request.GET.get("end_datetime", "")

    blocked_ips = BlockedIP.objects.all()

    if query:
        blocked_ips = blocked_ips.filter(Q(ip_address__icontains=query) | Q(reason__icontains=query))

    if start_datetime:
        dt = timezone.make_aware(datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M'))
        blocked_ips = blocked_ips.filter(banned_at__gte=dt)

    if end_datetime:
        dt = timezone.make_aware(datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M'))
        blocked_ips = blocked_ips.filter(banned_at__lte=dt)

    paginator = Paginator(blocked_ips, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    if request.method == "POST":
        ip_address = request.POST.get("ip_address")
        reason = request.POST.get("reason", "Manually blocked")

        if not re.match(IP_REGEX, ip_address):
            return render(request, "dashboard/blocked_ips.html", {
                "page_obj": page_obj,
                "query": query,
                "start_datetime": start_datetime,
                "end_datetime": end_datetime,
                "error": "Invalid IP address format!"
            })

        BlockedIP.objects.get_or_create(ip_address=ip_address, defaults={"reason": reason})
        return redirect("blocked-ips")

    return render(request, "dashboard/blocked_ips.html", {
        "page_obj": page_obj,
        "query": query,
        "start_datetime": start_datetime,
        "end_datetime": end_datetime,
    })


def toggle_ban_ip(request, ip_address):
    """Toggles ban status of a given IP address."""
    if request.method == "POST":
        blocked_ip = get_object_or_404(BlockedIP, ip_address=ip_address)
        blocked_ip.currently_banned = not blocked_ip.currently_banned
        blocked_ip.save()
        return redirect("blocked-ips")
    return HttpResponseForbidden("Invalid request")


def alerts_view(request):
    """Displays and filters alert logs."""
    query = request.GET.get('q')
    start_datetime = request.GET.get('start_datetime')
    end_datetime = request.GET.get('end_datetime')
    severity_filter = request.GET.get('severity')

    alerts = Alert.objects.all()

    if query:
        alerts = alerts.filter(Q(title__icontains=query) | Q(message__icontains=query))
    if start_datetime:
        dt = timezone.make_aware(datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M'))
        alerts = alerts.filter(created_at__gte=dt)
    if end_datetime:
        dt = timezone.make_aware(datetime.strptime(end_datetime, '%Y-%m-%dT%H:%M'))
        alerts = alerts.filter(created_at__lte=dt)
    if severity_filter and severity_filter != 'ALL':
        alerts = alerts.filter(severity=severity_filter)

    paginator = Paginator(alerts.order_by('-created_at'), 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/alerts.html', {
        'page_obj': page_obj,
        'query': query,
        'start_datetime': start_datetime,
        'end_datetime': end_datetime,
        'severity_filter': severity_filter,
    })


def system_settings(request):
    """Displays and updates system install/uninstall scripts."""
    install_script = SystemScript.objects.get(name="install")
    uninstall_script = SystemScript.objects.get(name="uninstall")

    if request.method == "POST":
        install_script.content = re.sub(r'\r\n', '\n', request.POST.get("install_script", ""))
        uninstall_script.content = re.sub(r'\r\n', '\n', request.POST.get("uninstall_script", ""))
        install_script.save()
        uninstall_script.save()
        messages.success(request, "Scripts updated successfully!")
        log_alert(request, "Scripts updated successfully!")
        return redirect("system-settings")

    return render(request, 'dashboard/system_settings.html', {
        "install_script": install_script.content,
        "uninstall_script": uninstall_script.content
    })


def managed_devices(request):
    """Displays all managed devices with last check-in times."""
    devices = ManagedDevice.objects.all().order_by('hostname')
    for device in devices:
        if device.last_check_in:
            device.time_diff_seconds = (timezone.now() - device.last_check_in).total_seconds()
        else:
            device.time_diff_seconds = float('inf')

    paginator = Paginator(devices, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard/managed_devices.html', {
        'page_obj': page_obj,
    })


def get_script(request, script_type):
    """Returns the content of a script for download."""
    script = SystemScript.objects.get(name=script_type)
    response = HttpResponse(script.content, content_type="text/plain")
    response["Content-Disposition"] = f'attachment; filename="{script_type}_script.sh"'
    return response


def generate_install_command(request):
    """Generates a unique install command with an install token."""
    token = uuid.uuid4()
    InstallToken.objects.create(
        token=token,
        expires_at=timezone.now() + timedelta(hours=1)
    )
    command = f"curl -sSL https://alarm.sgt.me.uk/install.sh | sudo bash -s -- {token}"
    return JsonResponse({"command": command, "token": str(token)})
