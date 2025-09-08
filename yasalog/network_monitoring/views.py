from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Max, Min
from django.db.models.functions import TruncHour
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from datetime import timedelta
import json
import re

from .models import NetworkDevice, NetworkLog, NetworkTraffic
from log_kayit.models import Company, CompanyUser

def parse_uptime_string(uptime_str):
    """Uptime string'ini timedelta'ya çevir
    Örnek: '5 gün, 3 saat' -> timedelta(days=5, hours=3)
    """
    if not uptime_str:
        return None
    
    # Regex pattern'leri
    day_pattern = r'(\d+)\s*gün'
    hour_pattern = r'(\d+)\s*saat'
    minute_pattern = r'(\d+)\s*dakika'
    
    days = 0
    hours = 0
    minutes = 0
    
    # Günleri bul
    day_match = re.search(day_pattern, uptime_str, re.IGNORECASE)
    if day_match:
        days = int(day_match.group(1))
    
    # Saatleri bul
    hour_match = re.search(hour_pattern, uptime_str, re.IGNORECASE)
    if hour_match:
        hours = int(hour_match.group(1))
    
    # Dakikaları bul
    minute_match = re.search(minute_pattern, uptime_str, re.IGNORECASE)
    if minute_match:
        minutes = int(minute_match.group(1))
    
    # Eğer hiçbir pattern bulunamazsa, sadece sayı varsa saat olarak kabul et
    if days == 0 and hours == 0 and minutes == 0:
        # Sadece sayı var mı kontrol et
        numbers = re.findall(r'\d+', uptime_str)
        if numbers:
            hours = int(numbers[0])
    
    return timedelta(days=days, hours=hours, minutes=minutes)

@login_required
def network_dashboard(request, company_id=None, company_slug=None):
    """Network monitoring ana dashboard"""
    
    print(f"DEBUG: network_dashboard çağrıldı - company_slug: {company_slug}, company_id: {company_id}")
    
    # Şirket kontrolü
    if company_slug:
        company = get_object_or_404(Company, slug=company_slug)
        print(f"DEBUG: Şirket bulundu: {company.name}")
    elif company_id:
        company = get_object_or_404(Company, id=company_id)
        print(f"DEBUG: Şirket bulundu: {company.name}")
    else:
        return HttpResponseForbidden("Company not found.")
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Cihaz durumları
    devices = NetworkDevice.objects.filter(company=company)
    device_stats = {
        'total': devices.count(),
        'online': devices.filter(status='ONLINE').count(),
        'offline': devices.filter(status='OFFLINE').count(),
        'warning': devices.filter(status='WARNING').count(),
        'critical': devices.filter(status='CRITICAL').count(),
    }
    
    # Son loglar
    recent_logs = NetworkLog.objects.filter(company=company).order_by('-timestamp')[:20]
    
    # Performans metrikleri
    performance_stats = {
        'avg_cpu': devices.aggregate(Avg('cpu_usage'))['cpu_usage__avg'] or 0,
        'avg_memory': devices.aggregate(Avg('memory_usage'))['memory_usage__avg'] or 0,
        'total_traffic': NetworkTraffic.objects.filter(
            company=company, 
            start_time__gte=timezone.now() - timedelta(hours=24)
        ).aggregate(
            total=Sum('bytes_sent') + Sum('bytes_received')
        )['total'] or 0,
    }
    
    # 24 saatlik performans grafiği
    last_24h = timezone.now() - timedelta(hours=24)
    hourly_stats = []
    
    for hour in range(24):
        hour_start = last_24h + timedelta(hours=hour)
        hour_end = hour_start + timedelta(hours=1)
        
        hour_logs = NetworkLog.objects.filter(
            company=company,
            timestamp__range=[hour_start, hour_end]
        )
        
        hour_traffic = NetworkTraffic.objects.filter(
            company=company,
            start_time__range=[hour_start, hour_end]
        )
        
        hourly_stats.append({
            'hour': hour_start.strftime('%H:00'),
            'logs_count': hour_logs.count(),
            'errors_count': hour_logs.filter(level__in=['ERROR', 'CRITICAL']).count(),
            'traffic_bytes': hour_traffic.aggregate(
                total=Sum('bytes_sent') + Sum('bytes_received')
            )['total'] or 0,
        })
    
    context = {
        'company': company,
        'device_stats': device_stats,
        'performance_stats': performance_stats,
        'hourly_stats': hourly_stats,
        'recent_logs': recent_logs,
        'devices': devices[:10],  # Son 10 cihaz
    }
    
    print(f"DEBUG: Context verileri:")
    print(f"  - company: {company.name}")
    print(f"  - devices count: {len(devices)}")
    print(f"  - device_stats: {device_stats}")
    print(f"  - template: network_monitoring/network_dashboard.html")
    
    return render(request, 'network_monitoring/network_dashboard.html', context)

@login_required
def device_detail(request, device_id):
    """Cihaz detay sayfası"""
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=device.company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Cihaz logları
    logs = NetworkLog.objects.filter(device=device).order_by('-timestamp')[:100]
    
    # Trafik istatistikleri
    traffic_stats = NetworkTraffic.objects.filter(device=device).aggregate(
        total_bytes=Sum('bytes_sent') + Sum('bytes_received'),
        total_packets=Sum('packets_sent') + Sum('packets_received'),
        avg_duration=Avg('duration')
    )
    
    context = {
        'device': device,
        'company': device.company,  # Company'yi context'e ekle
        'logs': logs,
        'traffic_stats': traffic_stats,
    }
    
    return render(request, 'network_monitoring/device_detail.html', context)

@login_required
def device_status_api(request, device_id):
    """Cihaz durum API endpoint'i (AJAX için)"""
    device = get_object_or_404(NetworkDevice, id=device_id)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=device.company).exists() or request.user.is_superuser):
        return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    # Cihaz durum bilgileri
    status_data = {
        'id': device.id,
        'name': device.name,
        'status': device.status,
        'ip_address': device.ip_address,
        'cpu_usage': device.cpu_usage,
        'memory_usage': device.memory_usage,
        'temperature': device.temperature,
        'uptime': str(device.uptime) if device.uptime else None,
        'last_seen': device.last_seen.isoformat(),
        'is_healthy': device.is_healthy,
    }
    
    return JsonResponse(status_data)

# FRONTEND ARAYÜZÜ İÇİN YENİ VIEW'LAR
@login_required
def device_list(request, company_slug):
    """Cihaz listesi - Frontend arayüzü"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    devices = NetworkDevice.objects.filter(company=company).order_by('-created_at')
    
    # Arama ve filtreleme
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    if search:
        devices = devices.filter(name__icontains=search)
    
    if status_filter:
        devices = devices.filter(status=status_filter)
    
    # Sayfalama
    paginator = Paginator(devices, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'search': search,
        'status_filter': status_filter,
        'status_choices': NetworkDevice.STATUS_CHOICES,
    }
    
    return render(request, 'network_monitoring/device_list.html', context)

@login_required
def device_add(request, company_slug):
    """Cihaz ekleme - Frontend arayüzü"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        device_type = request.POST.get('device_type')
        ip_address = request.POST.get('ip_address')
        mac_address = request.POST.get('mac_address')
        model = request.POST.get('model')
        manufacturer = request.POST.get('manufacturer')
        firmware_version = request.POST.get('firmware_version')
        serial_no = request.POST.get('serial_no')
        subnet_mask = request.POST.get('subnet_mask')
        gateway = request.POST.get('gateway')
        status = request.POST.get('status', 'OFFLINE')
        cpu_usage = request.POST.get('cpu_usage', 0)
        memory_usage = request.POST.get('memory_usage', 0)
        temperature = request.POST.get('temperature')
        uptime = request.POST.get('uptime')
        
        # Cihaz oluştur
        device = NetworkDevice.objects.create(
            company=company,
            name=name,
            device_type=device_type,
            ip_address=ip_address,
            mac_address=mac_address,
            model=model,
            manufacturer=manufacturer,
            firmware_version=firmware_version,
            serial_number=serial_no,
            subnet_mask=subnet_mask,
            gateway=gateway,
            status=status,
            cpu_usage=float(cpu_usage.strip()) if cpu_usage and cpu_usage.strip() else 0.0,
            memory_usage=float(memory_usage.strip()) if memory_usage and memory_usage.strip() else 0.0,
            temperature=float(temperature.strip()) if temperature and temperature.strip() else None,
            uptime=parse_uptime_string(uptime) if uptime else None,
        )
        
        messages.success(request, f'Cihaz "{name}" başarıyla eklendi.')
        return redirect('network_monitoring:device_list', company_slug=company.slug)
    
    context = {
        'company': company,
        'status_choices': NetworkDevice.STATUS_CHOICES,
        'device_types': NetworkDevice.DEVICE_TYPE_CHOICES,
    }
    
    return render(request, 'network_monitoring/device_add.html', context)

@login_required
def device_edit(request, company_slug, device_id):
    """Cihaz düzenleme - Frontend arayüzü"""
    company = get_object_or_404(Company, slug=company_slug)
    device = get_object_or_404(NetworkDevice, id=device_id, company=company)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Form verilerini güncelle
        device.name = request.POST.get('name')
        device.device_type = request.POST.get('device_type')
        device.ip_address = request.POST.get('ip_address')
        device.mac_address = request.POST.get('mac_address')
        device.model = request.POST.get('model')
        device.manufacturer = request.POST.get('manufacturer')
        device.firmware_version = request.POST.get('firmware_version')
        device.serial_number = request.POST.get('serial_no')
        device.subnet_mask = request.POST.get('subnet_mask')
        device.gateway = request.POST.get('gateway')
        device.status = request.POST.get('status')
        # CPU ve Memory kullanımı - boş string kontrolü
        cpu_usage = request.POST.get('cpu_usage', '0').strip()
        device.cpu_usage = float(cpu_usage) if cpu_usage else 0.0
        
        memory_usage = request.POST.get('memory_usage', '0').strip()
        device.memory_usage = float(memory_usage) if memory_usage else 0.0
        
        # Sıcaklık - boş string kontrolü
        temperature = request.POST.get('temperature', '').strip()
        device.temperature = float(temperature) if temperature else None
        # Uptime - string'i timedelta'ya çevir
        uptime_str = request.POST.get('uptime', '').strip()
        if uptime_str:
            try:
                # "5 gün, 3 saat" formatını parse et
                device.uptime = parse_uptime_string(uptime_str)
            except:
                device.uptime = None
        else:
            device.uptime = None
        
        device.save()
        
        messages.success(request, f'Cihaz "{device.name}" başarıyla güncellendi.')
        return redirect('network_monitoring:device_list', company_slug=company.slug)
    
    context = {
        'company': company,
        'device': device,
        'status_choices': NetworkDevice.STATUS_CHOICES,
        'device_types': NetworkDevice.DEVICE_TYPE_CHOICES,
    }
    
    return render(request, 'network_monitoring/device_edit.html', context)

@login_required
@require_http_methods(["POST"])
def device_delete(request, company_slug, device_id):
    """Cihaz silme - Frontend arayüzü"""
    company = get_object_or_404(Company, slug=company_slug)
    device = get_object_or_404(NetworkDevice, id=device_id, company=company)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    device_name = device.name
    device.delete()
    
    messages.success(request, f'Cihaz "{device_name}" başarıyla silindi.')
    return redirect('network_monitoring:device_list', company_slug=company.slug)
