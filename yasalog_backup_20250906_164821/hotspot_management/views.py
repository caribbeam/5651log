from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json

from log_kayit.models import Company
from .models import (
    HotspotConfiguration, BandwidthPolicy, HotspotUser, 
    UserSession, ContentFilter, AccessLog, HotspotMetrics
)


@login_required
def hotspot_dashboard(request, company_slug):
    """Hotspot yönetim dashboard'u"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Son 30 günlük veriler
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # Hotspot istatistikleri
    hotspots = HotspotConfiguration.objects.filter(company=company, is_active=True)
    total_hotspots = hotspots.count()
    
    # Kullanıcı istatistikleri
    users_stats = HotspotUser.objects.filter(
        company=company,
        created_at__gte=thirty_days_ago
    ).aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(is_active=True)),
        blocked=Count('id', filter=Q(is_blocked=True)),
        new_users=Count('id', filter=Q(created_at__gte=timezone.now() - timedelta(days=7)))
    )
    
    # Oturum istatistikleri
    sessions_stats = UserSession.objects.filter(
        user__company=company,
        start_time__gte=thirty_days_ago
    ).aggregate(
        total=Count('id'),
        active=Count('id', filter=Q(status='ACTIVE')),
        total_duration=Sum('duration_minutes'),
        avg_duration=Avg('duration_minutes')
    )
    
    # Bant genişliği kullanımı
    bandwidth_stats = UserSession.objects.filter(
        user__company=company,
        start_time__gte=thirty_days_ago
    ).aggregate(
        total_upload=Sum('bytes_uploaded'),
        total_download=Sum('bytes_downloaded'),
        total_bandwidth=Sum('total_bytes')
    )
    
    # İçerik filtreleme istatistikleri
    content_filter_stats = AccessLog.objects.filter(
        user__company=company,
        timestamp__gte=thirty_days_ago
    ).aggregate(
        total_requests=Count('id'),
        blocked_requests=Count('id', filter=Q(was_blocked=True)),
        allowed_requests=Count('id', filter=Q(was_blocked=False))
    )
    
    # Günlük kullanıcı sayısı (son 7 gün)
    daily_users = []
    for i in range(7):
        date = timezone.now() - timedelta(days=i)
        count = HotspotUser.objects.filter(
            company=company,
            created_at__date=date.date()
        ).count()
        daily_users.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    daily_users.reverse()
    
    # Aktif hotspot'lar
    active_hotspots = hotspots[:5]
    
    # Son kullanıcılar
    recent_users = HotspotUser.objects.filter(
        company=company
    ).order_by('-created_at')[:5]
    
    # Son oturumlar
    recent_sessions = UserSession.objects.filter(
        user__company=company
    ).order_by('-start_time')[:5]
    
    context = {
        'company': company,
        'total_hotspots': total_hotspots,
        'users_stats': users_stats,
        'sessions_stats': sessions_stats,
        'bandwidth_stats': bandwidth_stats,
        'content_filter_stats': content_filter_stats,
        'daily_users': daily_users,
        'active_hotspots': active_hotspots,
        'recent_users': recent_users,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'hotspot_management/hotspot_dashboard.html', context)


@login_required
def hotspot_configurations(request, company_slug):
    """Hotspot konfigürasyonları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Filtreleme
    is_active = request.GET.get('is_active', '')
    is_public = request.GET.get('is_public', '')
    search = request.GET.get('search', '')
    
    configurations = HotspotConfiguration.objects.filter(company=company)
    
    if is_active != '':
        configurations = configurations.filter(is_active=is_active == 'true')
    if is_public != '':
        configurations = configurations.filter(is_public=is_public == 'true')
    if search:
        configurations = configurations.filter(
            Q(name__icontains=search) |
            Q(ssid__icontains=search)
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', '-created_at')
    configurations = configurations.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(configurations, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'configurations': page_obj,
        'filters': {
            'is_active': is_active,
            'is_public': is_public,
            'search': search,
            'sort': sort_by
        }
    }
    
    return render(request, 'hotspot_management/configurations_list.html', context)


@login_required
def configuration_detail(request, company_slug, config_id):
    """Hotspot konfigürasyon detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    configuration = get_object_or_404(HotspotConfiguration, id=config_id, company=company)
    
    # İstatistikler
    total_users = HotspotUser.objects.filter(hotspot=configuration).count()
    active_users = HotspotUser.objects.filter(hotspot=configuration, is_active=True).count()
    total_sessions = UserSession.objects.filter(hotspot=configuration).count()
    
    # Son kullanıcılar
    recent_users = HotspotUser.objects.filter(
        hotspot=configuration
    ).order_by('-created_at')[:10]
    
    # Son oturumlar
    recent_sessions = UserSession.objects.filter(
        hotspot=configuration
    ).order_by('-start_time')[:10]
    
    context = {
        'company': company,
        'configuration': configuration,
        'total_users': total_users,
        'active_users': active_users,
        'total_sessions': total_sessions,
        'recent_users': recent_users,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'hotspot_management/configuration_detail.html', context)


@login_required
def users_list(request, company_slug):
    """Hotspot kullanıcıları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Filtreleme
    user_type = request.GET.get('user_type', '')
    is_active = request.GET.get('is_active', '')
    is_blocked = request.GET.get('is_blocked', '')
    search = request.GET.get('search', '')
    
    users = HotspotUser.objects.filter(company=company)
    
    if user_type:
        users = users.filter(user_type=user_type)
    if is_active != '':
        users = users.filter(is_active=is_active == 'true')
    if is_blocked != '':
        users = users.filter(is_blocked=is_blocked == 'true')
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(mac_address__icontains=search) |
            Q(ip_address__icontains=search)
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', '-created_at')
    users = users.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'users': page_obj,
        'filters': {
            'user_type': user_type,
            'is_active': is_active,
            'is_blocked': is_blocked,
            'search': search,
            'sort': sort_by
        },
        'user_types': HotspotUser.USER_TYPES,
    }
    
    return render(request, 'hotspot_management/users_list.html', context)


@login_required
def user_detail(request, company_slug, user_id):
    """Hotspot kullanıcı detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    user = get_object_or_404(HotspotUser, id=user_id, company=company)
    
    # Kullanıcı oturumları
    sessions = UserSession.objects.filter(user=user).order_by('-start_time')
    
    # Erişim logları
    access_logs = AccessLog.objects.filter(user=user).order_by('-timestamp')[:50]
    
    # İstatistikler
    total_sessions = sessions.count()
    total_duration = sessions.aggregate(total=Sum('duration_minutes'))['total'] or 0
    total_bandwidth = sessions.aggregate(total=Sum('total_bytes'))['total'] or 0
    
    context = {
        'company': company,
        'user': user,
        'sessions': sessions[:10],
        'access_logs': access_logs,
        'total_sessions': total_sessions,
        'total_duration': total_duration,
        'total_bandwidth': total_bandwidth,
    }
    
    return render(request, 'hotspot_management/user_detail.html', context)


@login_required
def sessions_list(request, company_slug):
    """Kullanıcı oturumları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Filtreleme
    status = request.GET.get('status', '')
    hotspot = request.GET.get('hotspot', '')
    search = request.GET.get('search', '')
    
    sessions = UserSession.objects.filter(user__company=company)
    
    if status:
        sessions = sessions.filter(status=status)
    if hotspot:
        sessions = sessions.filter(hotspot_id=hotspot)
    if search:
        sessions = sessions.filter(
            Q(session_id__icontains=search) |
            Q(user__username__icontains=search) |
            Q(hotspot__name__icontains=search)
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', '-start_time')
    sessions = sessions.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(sessions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Hotspot seçenekleri
    hotspots = HotspotConfiguration.objects.filter(company=company, is_active=True)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'sessions': page_obj,
        'hotspots': hotspots,
        'filters': {
            'status': status,
            'hotspot': hotspot,
            'search': search,
            'sort': sort_by
        },
        'session_statuses': UserSession.SESSION_STATUS,
    }
    
    return render(request, 'hotspot_management/sessions_list.html', context)


@login_required
def content_filters(request, company_slug):
    """İçerik filtreleme kuralları"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Filtreleme
    filter_type = request.GET.get('filter_type', '')
    action = request.GET.get('action', '')
    is_active = request.GET.get('is_active', '')
    search = request.GET.get('search', '')
    
    filters = ContentFilter.objects.filter(company=company)
    
    if filter_type:
        filters = filters.filter(filter_type=filter_type)
    if action:
        filters = filters.filter(action=action)
    if is_active != '':
        filters = filters.filter(is_active=is_active == 'true')
    if search:
        filters = filters.filter(
            Q(name__icontains=search) |
            Q(value__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', 'priority')
    filters = filters.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(filters, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'filters': page_obj,
        'filter_filters': {
            'filter_type': filter_type,
            'action': action,
            'is_active': is_active,
            'search': search,
            'sort': sort_by
        },
        'filter_types': ContentFilter.FILTER_TYPES,
        'action_types': ContentFilter.ACTION_TYPES,
    }
    
    return render(request, 'hotspot_management/content_filters.html', context)


@login_required
def access_logs(request, company_slug):
    """Erişim logları"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Filtreleme
    was_blocked = request.GET.get('was_blocked', '')
    domain = request.GET.get('domain', '')
    search = request.GET.get('search', '')
    
    logs = AccessLog.objects.filter(user__company=company)
    
    if was_blocked != '':
        logs = logs.filter(was_blocked=was_blocked == 'true')
    if domain:
        logs = logs.filter(domain__icontains=domain)
    if search:
        logs = logs.filter(
            Q(url__icontains=search) |
            Q(domain__icontains=search) |
            Q(ip_address__icontains=search) |
            Q(user__username__icontains=search)
        )
    
    # Sıralama
    sort_by = request.GET.get('sort', '-timestamp')
    logs = logs.order_by(sort_by)
    
    # Sayfalama
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'logs': page_obj,
        'filters': {
            'was_blocked': was_blocked,
            'domain': domain,
            'search': search,
            'sort': sort_by
        }
    }
    
    return render(request, 'hotspot_management/access_logs.html', context)


@login_required
def api_hotspot_stats(request, company_slug):
    """Hotspot istatistikleri API endpoint'i"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Son 7 günlük veriler
    seven_days_ago = timezone.now() - timedelta(days=7)
    
    # Günlük kullanıcı sayısı
    daily_users = []
    for i in range(7):
        date = timezone.now() - timedelta(days=i)
        count = HotspotUser.objects.filter(
            company=company,
            created_at__date=date.date()
        ).count()
        daily_users.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    daily_users.reverse()
    
    # Kullanıcı tiplerine göre dağılım
    user_types = HotspotUser.objects.filter(
        company=company,
        created_at__gte=seven_days_ago
    ).values('user_type').annotate(count=Count('id')).order_by('-count')
    
    # Bant genişliği kullanımı
    bandwidth_usage = UserSession.objects.filter(
        user__company=company,
        start_time__gte=seven_days_ago
    ).aggregate(
        total_upload=Sum('bytes_uploaded'),
        total_download=Sum('bytes_downloaded'),
        total_bandwidth=Sum('total_bytes')
    )
    
    return JsonResponse({
        'daily_users': daily_users,
        'user_types': list(user_types),
        'bandwidth_usage': bandwidth_usage,
    })
