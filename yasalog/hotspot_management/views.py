from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum, Avg
from django.utils import timezone
from django.contrib import messages
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
def configuration_add(request, company_slug):
    """Yeni hotspot konfigürasyonu ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        ssid = request.POST.get('ssid')
        password = request.POST.get('password')
        is_active = request.POST.get('is_active') == 'on'
        is_public = request.POST.get('is_public') == 'on'
        max_users = request.POST.get('max_users', 0)
        session_timeout = request.POST.get('session_timeout', 0)
        bandwidth_limit = request.POST.get('bandwidth_limit', 0)
        description = request.POST.get('description', '')
        
        # Validation
        if not name or not ssid:
            messages.error(request, 'Ad ve SSID alanları zorunludur.')
        else:
            try:
                # Yeni konfigürasyon oluştur
                configuration = HotspotConfiguration.objects.create(
                    company=company,
                    name=name,
                    ssid=ssid,
                    password=password,
                    is_active=is_active,
                    is_public=is_public,
                    max_concurrent_users=int(max_users) if max_users else 100,
                    session_timeout_hours=int(session_timeout) if session_timeout else 24,
                    max_bandwidth_mbps=int(bandwidth_limit) if bandwidth_limit else 10
                )
                
                messages.success(request, f'Hotspot konfigürasyonu "{name}" başarıyla oluşturuldu.')
                return redirect('hotspot_management:configuration_detail', company.slug, configuration.id)
                
            except Exception as e:
                messages.error(request, f'Konfigürasyon oluşturulurken hata oluştu: {str(e)}')
    
    context = {
        'company': company,
    }
    
    return render(request, 'hotspot_management/configuration_add.html', context)


@login_required
def configuration_edit(request, company_slug, config_id):
    """Hotspot konfigürasyonu düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    configuration = get_object_or_404(HotspotConfiguration, id=config_id, company=company)
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        ssid = request.POST.get('ssid')
        password = request.POST.get('password')
        is_active = request.POST.get('is_active') == 'on'
        is_public = request.POST.get('is_public') == 'on'
        max_users = request.POST.get('max_users', 0)
        session_timeout = request.POST.get('session_timeout', 0)
        bandwidth_limit = request.POST.get('bandwidth_limit', 0)
        
        # Validation
        if not name or not ssid:
            messages.error(request, 'Ad ve SSID alanları zorunludur.')
        else:
            try:
                # Konfigürasyonu güncelle
                configuration.name = name
                configuration.ssid = ssid
                configuration.password = password
                configuration.is_active = is_active
                configuration.is_public = is_public
                configuration.max_concurrent_users = int(max_users) if max_users else 100
                configuration.session_timeout_hours = int(session_timeout) if session_timeout else 24
                configuration.max_bandwidth_mbps = int(bandwidth_limit) if bandwidth_limit else 10
                configuration.save()
                
                messages.success(request, f'Hotspot konfigürasyonu "{name}" başarıyla güncellendi.')
                return redirect('hotspot_management:configuration_detail', company.slug, configuration.id)
                
            except Exception as e:
                messages.error(request, f'Konfigürasyon güncellenirken hata oluştu: {str(e)}')
    
    context = {
        'company': company,
        'configuration': configuration,
    }
    
    return render(request, 'hotspot_management/configuration_edit.html', context)


@login_required
def configuration_delete(request, company_slug, config_id):
    """Hotspot konfigürasyonu silme"""
    company = get_object_or_404(Company, slug=company_slug)
    configuration = get_object_or_404(HotspotConfiguration, id=config_id, company=company)
    
    if request.method == 'POST':
        try:
            config_name = configuration.name
            configuration.delete()
            messages.success(request, f'Hotspot konfigürasyonu "{config_name}" başarıyla silindi.')
            return redirect('hotspot_management:configurations_list', company.slug)
        except Exception as e:
            messages.error(request, f'Konfigürasyon silinirken hata oluştu: {str(e)}')
            return redirect('hotspot_management:configuration_detail', company.slug, config_id)
    
    # İlişkili verileri kontrol et
    total_users = HotspotUser.objects.filter(hotspot=configuration).count()
    total_sessions = UserSession.objects.filter(hotspot=configuration).count()
    
    context = {
        'company': company,
        'configuration': configuration,
        'total_users': total_users,
        'total_sessions': total_sessions,
    }
    
    return render(request, 'hotspot_management/configuration_delete.html', context)


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
def toggle_user_status(request, user_id):
    """Kullanıcı durumunu değiştir"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Sadece POST metodu kabul edilir'})
    
    try:
        user = get_object_or_404(HotspotUser, id=user_id)
        
        # Yetki kontrolü
        if not (request.user.is_superuser or 
                hasattr(request.user, 'companyuser') and 
                request.user.companyuser.company == user.company):
            return JsonResponse({'success': False, 'message': 'Yetkisiz erişim'})
        
        import json
        data = json.loads(request.body)
        is_active = data.get('is_active')
        
        if is_active is None:
            return JsonResponse({'success': False, 'message': 'is_active parametresi gerekli'})
        
        user.is_active = is_active
        user.save()
        
        status_text = 'aktifleştirildi' if is_active else 'pasifleştirildi'
        return JsonResponse({'success': True, 'message': f'Kullanıcı başarıyla {status_text}'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})


@login_required
def toggle_user_block(request, user_id):
    """Kullanıcı engelini değiştir"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Sadece POST metodu kabul edilir'})
    
    try:
        user = get_object_or_404(HotspotUser, id=user_id)
        
        # Yetki kontrolü
        if not (request.user.is_superuser or 
                hasattr(request.user, 'companyuser') and 
                request.user.companyuser.company == user.company):
            return JsonResponse({'success': False, 'message': 'Yetkisiz erişim'})
        
        import json
        data = json.loads(request.body)
        is_blocked = data.get('is_blocked')
        
        if is_blocked is None:
            return JsonResponse({'success': False, 'message': 'is_blocked parametresi gerekli'})
        
        user.is_blocked = is_blocked
        user.save()
        
        status_text = 'engellendi' if is_blocked else 'engeli kaldırıldı'
        return JsonResponse({'success': True, 'message': f'Kullanıcı başarıyla {status_text}'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})


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
def session_add(request, company_slug):
    """Yeni hotspot oturumu ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        # Form verilerini al
        user_id = request.POST.get('user')
        hotspot_id = request.POST.get('hotspot')
        session_id = request.POST.get('session_id')
        status = request.POST.get('status', 'ACTIVE')
        bytes_uploaded = request.POST.get('bytes_uploaded', 0)
        bytes_downloaded = request.POST.get('bytes_downloaded', 0)
        duration_minutes = request.POST.get('duration_minutes', 0)
        
        # Validation
        if not user_id or not hotspot_id:
            messages.error(request, 'Kullanıcı ve Hotspot alanları zorunludur.')
        else:
            try:
                # Kullanıcı ve hotspot'u al
                user = get_object_or_404(HotspotUser, id=user_id, company=company)
                hotspot = get_object_or_404(HotspotConfiguration, id=hotspot_id, company=company)
                
                # Session ID oluştur
                if not session_id:
                    import uuid
                    session_id = str(uuid.uuid4())
                
                # Yeni oturum oluştur
                session = UserSession.objects.create(
                    user=user,
                    hotspot=hotspot,
                    session_id=session_id,
                    status=status,
                    bytes_uploaded=int(bytes_uploaded) if bytes_uploaded else 0,
                    bytes_downloaded=int(bytes_downloaded) if bytes_downloaded else 0,
                    total_bytes=int(bytes_uploaded) if bytes_uploaded else 0 + int(bytes_downloaded) if bytes_downloaded else 0,
                    duration_minutes=int(duration_minutes) if duration_minutes else 0
                )
                
                messages.success(request, f'Hotspot oturumu başarıyla oluşturuldu.')
                return redirect('hotspot_management:sessions_list', company.slug)
                
            except Exception as e:
                messages.error(request, f'Oturum oluşturulurken hata oluştu: {str(e)}')
    
    # Kullanıcılar ve hotspot'ları al
    users = HotspotUser.objects.filter(company=company, is_active=True)
    hotspots = HotspotConfiguration.objects.filter(company=company, is_active=True)
    
    context = {
        'company': company,
        'users': users,
        'hotspots': hotspots,
    }
    
    return render(request, 'hotspot_management/session_add.html', context)


@login_required
def session_edit(request, company_slug, session_id):
    """Hotspot oturumu düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    session = get_object_or_404(UserSession, id=session_id, user__company=company)
    
    if request.method == 'POST':
        # Form verilerini al
        user_id = request.POST.get('user')
        hotspot_id = request.POST.get('hotspot')
        session_id_field = request.POST.get('session_id')
        status = request.POST.get('status')
        bytes_uploaded = request.POST.get('bytes_uploaded', 0)
        bytes_downloaded = request.POST.get('bytes_downloaded', 0)
        duration_minutes = request.POST.get('duration_minutes', 0)
        
        # Validation
        if not user_id or not hotspot_id:
            messages.error(request, 'Kullanıcı ve Hotspot alanları zorunludur.')
        else:
            try:
                # Kullanıcı ve hotspot'u al
                user = get_object_or_404(HotspotUser, id=user_id, company=company)
                hotspot = get_object_or_404(HotspotConfiguration, id=hotspot_id, company=company)
                
                # Session'u güncelle
                session.user = user
                session.hotspot = hotspot
                session.session_id = session_id_field
                session.status = status
                session.bytes_uploaded = int(bytes_uploaded) if bytes_uploaded else 0
                session.bytes_downloaded = int(bytes_downloaded) if bytes_downloaded else 0
                session.total_bytes = int(bytes_uploaded) if bytes_uploaded else 0 + int(bytes_downloaded) if bytes_downloaded else 0
                session.duration_minutes = int(duration_minutes) if duration_minutes else 0
                session.save()
                
                messages.success(request, f'Hotspot oturumu başarıyla güncellendi.')
                return redirect('hotspot_management:sessions_list', company.slug)
                
            except Exception as e:
                messages.error(request, f'Oturum güncellenirken hata oluştu: {str(e)}')
    
    # Kullanıcılar ve hotspot'ları al
    users = HotspotUser.objects.filter(company=company, is_active=True)
    hotspots = HotspotConfiguration.objects.filter(company=company, is_active=True)
    
    context = {
        'company': company,
        'session': session,
        'users': users,
        'hotspots': hotspots,
    }
    
    return render(request, 'hotspot_management/session_edit.html', context)


@login_required
def session_delete(request, company_slug, session_id):
    """Hotspot oturumu silme"""
    company = get_object_or_404(Company, slug=company_slug)
    session = get_object_or_404(UserSession, id=session_id, user__company=company)
    
    if request.method == 'POST':
        try:
            session_id_backup = session.id
            session.delete()
            messages.success(request, f'Hotspot oturumu (ID: {session_id_backup}) başarıyla silindi.')
            return redirect('hotspot_management:sessions_list', company.slug)
        except Exception as e:
            messages.error(request, f'Oturum silinirken hata oluştu: {str(e)}')
    
    context = {
        'company': company,
        'session': session,
    }
    
    return render(request, 'hotspot_management/session_delete.html', context)


@login_required
def content_filter_add(request, company_slug):
    """Yeni içerik filtresi ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        filter_type = request.POST.get('filter_type')
        value = request.POST.get('pattern')  # pattern field'ı value olarak kullanılıyor
        action = request.POST.get('action', 'BLOCK')
        is_active = request.POST.get('is_active') == 'on'
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 1)
        
        # Validation
        if not name or not filter_type or not value:
            messages.error(request, 'Ad, Filtre Tipi ve Filtre Değeri alanları zorunludur.')
        else:
            try:
                # Yeni içerik filtresi oluştur
                content_filter = ContentFilter.objects.create(
                    company=company,
                    name=name,
                    filter_type=filter_type,
                    value=value,
                    action=action,
                    is_active=is_active,
                    description=description,
                    priority=int(priority) if priority else 1
                )
                
                messages.success(request, f'İçerik filtresi "{name}" başarıyla oluşturuldu.')
                return redirect('hotspot_management:content_filters', company.slug)
                
            except Exception as e:
                messages.error(request, f'Filtre oluşturulurken hata oluştu: {str(e)}')
    
    # Filtre tiplerini al
    filter_types = ContentFilter.FILTER_TYPES
    
    context = {
        'company': company,
        'filter_types': filter_types,
    }
    
    return render(request, 'hotspot_management/content_filter_add.html', context)


@login_required
def content_filter_edit(request, company_slug, filter_id):
    """İçerik filtresi düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    content_filter = get_object_or_404(ContentFilter, id=filter_id, company=company)
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        filter_type = request.POST.get('filter_type')
        value = request.POST.get('pattern')  # pattern field'ı value olarak kullanılıyor
        action = request.POST.get('action', 'BLOCK')
        is_active = request.POST.get('is_active') == 'on'
        description = request.POST.get('description', '')
        priority = request.POST.get('priority', 1)
        
        # Validation
        if not name or not filter_type or not value:
            messages.error(request, 'Ad, Filtre Tipi ve Filtre Değeri alanları zorunludur.')
        else:
            try:
                # Filtreyi güncelle
                content_filter.name = name
                content_filter.filter_type = filter_type
                content_filter.value = value
                content_filter.action = action
                content_filter.is_active = is_active
                content_filter.description = description
                content_filter.priority = int(priority) if priority else 1
                content_filter.save()
                
                messages.success(request, f'İçerik filtresi "{name}" başarıyla güncellendi.')
                return redirect('hotspot_management:content_filters', company.slug)
                
            except Exception as e:
                messages.error(request, f'Filtre güncellenirken hata oluştu: {str(e)}')
    
    # Filtre tiplerini al
    filter_types = ContentFilter.FILTER_TYPES
    
    context = {
        'company': company,
        'content_filter': content_filter,
        'filter_types': filter_types,
    }
    
    return render(request, 'hotspot_management/content_filter_edit.html', context)


@login_required
def content_filter_delete(request, company_slug, filter_id):
    """İçerik filtresi silme"""
    company = get_object_or_404(Company, slug=company_slug)
    content_filter = get_object_or_404(ContentFilter, id=filter_id, company=company)
    
    if request.method == 'POST':
        try:
            filter_name = content_filter.name
            content_filter.delete()
            messages.success(request, f'İçerik filtresi "{filter_name}" başarıyla silindi.')
            return redirect('hotspot_management:content_filters', company.slug)
        except Exception as e:
            messages.error(request, f'Filtre silinirken hata oluştu: {str(e)}')
    
    context = {
        'company': company,
        'content_filter': content_filter,
    }
    
    return render(request, 'hotspot_management/content_filter_delete.html', context)


@login_required
def access_log_add(request, company_slug):
    """Yeni erişim logu ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        # Form verilerini al
        user_id = request.POST.get('user')
        session_id = request.POST.get('session')
        url = request.POST.get('url')
        domain = request.POST.get('domain', '')
        ip_address = request.POST.get('ip_address', '')
        content_filter_id = request.POST.get('content_filter', '')
        was_blocked = request.POST.get('was_blocked') == 'on'
        
        # Validation
        if not user_id or not session_id or not url:
            messages.error(request, 'Kullanıcı, Oturum ve URL alanları zorunludur.')
        else:
            try:
                # Kullanıcı ve oturumu al
                user = get_object_or_404(HotspotUser, id=user_id, company=company)
                session = get_object_or_404(UserSession, id=session_id, user=user)
                
                # Domain'i URL'den çıkar
                if not domain and url:
                    try:
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc
                    except:
                        domain = ''
                
                # IP adresini kullanıcıdan al
                if not ip_address:
                    ip_address = user.ip_address or '127.0.0.1'
                
                # Content filter'ı al
                content_filter = None
                if content_filter_id:
                    content_filter = get_object_or_404(ContentFilter, id=content_filter_id, company=company)
                
                # Yeni erişim logu oluştur
                access_log = AccessLog.objects.create(
                    user=user,
                    session=session,
                    url=url,
                    domain=domain,
                    ip_address=ip_address,
                    content_filter=content_filter,
                    was_blocked=was_blocked
                )
                
                messages.success(request, f'Erişim logu başarıyla oluşturuldu.')
                return redirect('hotspot_management:access_logs', company.slug)
                
            except Exception as e:
                messages.error(request, f'Log oluşturulurken hata oluştu: {str(e)}')
    
    # Kullanıcılar, oturumlar ve content filter'ları al
    users = HotspotUser.objects.filter(company=company, is_active=True)
    sessions = UserSession.objects.filter(user__company=company)
    content_filters = ContentFilter.objects.filter(company=company, is_active=True)
    
    context = {
        'company': company,
        'users': users,
        'sessions': sessions,
        'content_filters': content_filters,
    }
    
    return render(request, 'hotspot_management/access_log_add.html', context)


@login_required
def access_log_edit(request, company_slug, log_id):
    """Erişim logu düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    access_log = get_object_or_404(AccessLog, id=log_id, user__company=company)
    
    if request.method == 'POST':
        # Form verilerini al
        user_id = request.POST.get('user')
        session_id = request.POST.get('session')
        url = request.POST.get('url')
        domain = request.POST.get('domain', '')
        ip_address = request.POST.get('ip_address', '')
        content_filter_id = request.POST.get('content_filter', '')
        was_blocked = request.POST.get('was_blocked') == 'on'
        
        # Validation
        if not user_id or not session_id or not url:
            messages.error(request, 'Kullanıcı, Oturum ve URL alanları zorunludur.')
        else:
            try:
                # Kullanıcı ve oturumu al
                user = get_object_or_404(HotspotUser, id=user_id, company=company)
                session = get_object_or_404(UserSession, id=session_id, user=user)
                
                # Domain'i URL'den çıkar
                if not domain and url:
                    try:
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        domain = parsed_url.netloc
                    except:
                        domain = ''
                
                # IP adresini kullanıcıdan al
                if not ip_address:
                    ip_address = user.ip_address or '127.0.0.1'
                
                # Content filter'ı al
                content_filter = None
                if content_filter_id:
                    content_filter = get_object_or_404(ContentFilter, id=content_filter_id, company=company)
                
                # Erişim logunu güncelle
                access_log.user = user
                access_log.session = session
                access_log.url = url
                access_log.domain = domain
                access_log.ip_address = ip_address
                access_log.content_filter = content_filter
                access_log.was_blocked = was_blocked
                access_log.save()
                
                messages.success(request, f'Erişim logu başarıyla güncellendi.')
                return redirect('hotspot_management:access_logs', company.slug)
                
            except Exception as e:
                messages.error(request, f'Log güncellenirken hata oluştu: {str(e)}')
    
    # Kullanıcılar, oturumlar ve content filter'ları al
    users = HotspotUser.objects.filter(company=company, is_active=True)
    sessions = UserSession.objects.filter(user__company=company)
    content_filters = ContentFilter.objects.filter(company=company, is_active=True)
    
    context = {
        'company': company,
        'access_log': access_log,
        'users': users,
        'sessions': sessions,
        'content_filters': content_filters,
    }
    
    return render(request, 'hotspot_management/access_log_edit.html', context)


@login_required
def access_log_delete(request, company_slug, log_id):
    """Erişim logu silme"""
    company = get_object_or_404(Company, slug=company_slug)
    access_log = get_object_or_404(AccessLog, id=log_id, user__company=company)
    
    if request.method == 'POST':
        try:
            log_url = access_log.url
            access_log.delete()
            messages.success(request, f'Erişim logu "{log_url}" başarıyla silindi.')
            return redirect('hotspot_management:access_logs', company.slug)
        except Exception as e:
            messages.error(request, f'Log silinirken hata oluştu: {str(e)}')
    
    context = {
        'company': company,
        'access_log': access_log,
    }
    
    return render(request, 'hotspot_management/access_log_delete.html', context)


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
        'content_filters': page_obj,  # Template'de content_filters kullanılıyor
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
