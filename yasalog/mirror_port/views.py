"""
Mirror Port Views
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from log_kayit.models import Company, CompanyUser
from .models import MirrorConfiguration, MirrorDevice, VLANConfiguration, MirrorTraffic


@login_required
def mirror_dashboard(request, company_slug):
    """Mirror port dashboard'u"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    context = {
        'company': company,
    }
    
    return render(request, 'mirror_port/dashboard.html', context)


@login_required
def configurations_list(request, company_slug):
    """Mirror konfigürasyonları listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut konfigürasyonları al
    configurations = MirrorConfiguration.objects.filter(company=company).order_by('-created_at')
    
    context = {
        'company': company,
        'configurations': configurations,
    }
    
    return render(request, 'mirror_port/configurations_list.html', context)


@login_required
def configuration_add(request, company_slug):
    """Yeni mirror konfigürasyonu ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut cihazları al
    devices = MirrorDevice.objects.filter(company=company, is_online=True)
    vlans = VLANConfiguration.objects.filter(company=company, is_active=True)
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        config_type = request.POST.get('config_type')
        source_ports = request.POST.get('source_ports')
        source_vlans = request.POST.get('source_vlans', '')
        destination_port = request.POST.get('destination_port')
        destination_ip = request.POST.get('destination_ip', '')
        direction = request.POST.get('direction', 'BOTH')
        protocol_filter = request.POST.get('protocol_filter', '')
        max_bandwidth = int(request.POST.get('max_bandwidth', 1000))
        buffer_size = int(request.POST.get('buffer_size', 100))
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            # Yeni konfigürasyon oluştur
            config = MirrorConfiguration.objects.create(
                company=company,
                name=name,
                config_type=config_type,
                source_ports=source_ports,
                source_vlans=source_vlans,
                destination_port=destination_port,
                destination_ip=destination_ip if destination_ip else None,
                direction=direction,
                protocol_filter=protocol_filter,
                max_bandwidth=max_bandwidth,
                buffer_size=buffer_size,
                is_active=is_active
            )
            
            messages.success(request, f"Konfigürasyon '{name}' başarıyla oluşturuldu.")
            return redirect('mirror_port:configuration_detail', company_slug=company.slug, config_id=config.id)
            
        except Exception as e:
            messages.error(request, f"Konfigürasyon oluşturulamadı: {str(e)}")
    
    context = {
        'company': company,
        'devices': devices,
        'vlans': vlans,
    }
    
    return render(request, 'mirror_port/configuration_add.html', context)


@login_required
def configuration_detail(request, company_slug, config_id):
    """Mirror konfigürasyon detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Konfigürasyonu al
    configuration = get_object_or_404(MirrorConfiguration, id=config_id, company=company)
    
    context = {
        'company': company,
        'configuration': configuration,
    }
    
    return render(request, 'mirror_port/configuration_detail.html', context)


@login_required
def vlans_list(request, company_slug):
    """VLAN listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut VLAN'ları al
    vlans = VLANConfiguration.objects.filter(company=company).order_by('vlan_id')
    
    context = {
        'company': company,
        'vlans': vlans,
    }
    
    return render(request, 'mirror_port/vlans_list.html', context)


@login_required
def vlan_add(request, company_slug):
    """Yeni VLAN konfigürasyonu ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut mirror konfigürasyonlarını al
    mirror_configs = MirrorConfiguration.objects.filter(company=company, is_active=True)
    
    if request.method == 'POST':
        # Form verilerini al
        vlan_id = int(request.POST.get('vlan_id'))
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        subnet = request.POST.get('subnet')
        gateway = request.POST.get('gateway', '')
        dns_servers = request.POST.get('dns_servers', '')
        mirror_enabled = request.POST.get('mirror_enabled') == 'on'
        mirror_config_id = request.POST.get('mirror_config', '')
        is_active = request.POST.get('is_active') == 'on'
        
        try:
            # Mirror config seçimi
            mirror_config = None
            if mirror_config_id and mirror_config_id != '':
                mirror_config = MirrorConfiguration.objects.get(id=mirror_config_id)
            
            # Yeni VLAN oluştur
            vlan = VLANConfiguration.objects.create(
                company=company,
                vlan_id=vlan_id,
                name=name,
                description=description,
                subnet=subnet,
                gateway=gateway if gateway else None,
                dns_servers=dns_servers,
                mirror_enabled=mirror_enabled,
                mirror_config=mirror_config,
                is_active=is_active
            )
            
            messages.success(request, f"VLAN '{name}' (ID: {vlan_id}) başarıyla oluşturuldu.")
            return redirect('mirror_port:vlan_detail', company_slug=company.slug, vlan_id=vlan.id)
            
        except Exception as e:
            messages.error(request, f"VLAN oluşturulamadı: {str(e)}")
    
    context = {
        'company': company,
        'mirror_configs': mirror_configs,
    }
    
    return render(request, 'mirror_port/vlan_add.html', context)


@login_required
def vlan_detail(request, company_slug, vlan_id):
    """VLAN detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # VLAN'ı al
    vlan = get_object_or_404(VLANConfiguration, id=vlan_id, company=company)
    
    context = {
        'company': company,
        'vlan': vlan,
    }
    
    return render(request, 'mirror_port/vlan_detail.html', context)


@login_required
def vlan_edit(request, company_slug, vlan_id):
    """VLAN düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # VLAN'ı al
    vlan = get_object_or_404(VLANConfiguration, id=vlan_id, company=company)
    
    if request.method == 'POST':
        vlan_id_value = request.POST.get('vlan_id')
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        subnet = request.POST.get('subnet')
        gateway = request.POST.get('gateway', '')
        dns_servers = request.POST.get('dns_servers', '')
        mirror_enabled = request.POST.get('mirror_enabled') == 'on'
        mirror_config_id = request.POST.get('mirror_config', '')
        is_active = request.POST.get('is_active') == 'on'
        
        if not vlan_id_value or not name or not subnet:
            messages.error(request, 'VLAN ID, Ad ve Subnet alanları zorunludur.')
        else:
            try:
                vlan_id_int = int(vlan_id_value)
                if vlan_id_int < 1 or vlan_id_int > 4094:
                    messages.error(request, 'VLAN ID 1-4094 arasında olmalıdır.')
                else:
                    # Aynı VLAN ID kontrolü (kendisi hariç)
                    if VLANConfiguration.objects.filter(company=company, vlan_id=vlan_id_int).exclude(id=vlan.id).exists():
                        messages.error(request, 'Bu VLAN ID zaten kullanılıyor.')
                    else:
                        vlan.vlan_id = vlan_id_int
                        vlan.name = name
                        vlan.description = description
                        vlan.subnet = subnet
                        vlan.gateway = gateway if gateway else None
                        vlan.dns_servers = dns_servers
                        vlan.mirror_enabled = mirror_enabled
                        vlan.is_active = is_active
                        
                        # Mirror konfigürasyonu
                        if mirror_config_id:
                            mirror_config = get_object_or_404(MirrorConfiguration, id=mirror_config_id, company=company)
                            vlan.mirror_config = mirror_config
                        else:
                            vlan.mirror_config = None
                        
                        vlan.save()
                        messages.success(request, f'VLAN "{vlan.name}" başarıyla güncellendi.')
                        return redirect('mirror_port:vlans_list', company.slug)
                        
            except ValueError:
                messages.error(request, 'VLAN ID geçerli bir sayı olmalıdır.')
            except Exception as e:
                messages.error(request, f'VLAN güncellenirken hata oluştu: {str(e)}')
    
    # Mirror konfigürasyonları
    mirror_configs = MirrorConfiguration.objects.filter(company=company, is_active=True)
    
    context = {
        'company': company,
        'vlan': vlan,
        'mirror_configs': mirror_configs,
    }
    
    return render(request, 'mirror_port/vlan_edit.html', context)


@login_required
def vlan_delete(request, company_slug, vlan_id):
    """VLAN silme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # VLAN'ı al
    vlan = get_object_or_404(VLANConfiguration, id=vlan_id, company=company)
    
    if request.method == 'POST':
        try:
            vlan_name = vlan.name
            vlan.delete()
            messages.success(request, f'VLAN "{vlan_name}" başarıyla silindi.')
            return redirect('mirror_port:vlans_list', company.slug)
        except Exception as e:
            messages.error(request, f'VLAN silinirken hata oluştu: {str(e)}')
            return redirect('mirror_port:vlans_list', company.slug)
    
    context = {
        'company': company,
        'vlan': vlan,
    }
    
    return render(request, 'mirror_port/vlan_delete.html', context)


@login_required
def traffic_analysis(request, company_slug):
    """Trafik analizi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    from datetime import datetime, timedelta
    from django.db.models import Count, Sum, Avg
    
    # Son 24 saatlik veriler
    end_time = timezone.now()
    start_time = end_time - timedelta(hours=24)
    
    # Trafik istatistikleri
    total_traffic = MirrorTraffic.objects.filter(company=company, timestamp__gte=start_time)
    
    # Protokol bazlı analiz
    protocol_stats = total_traffic.values('protocol').annotate(
        count=Count('id'),
        bytes_sent=Sum('bytes_sent'),
        bytes_received=Sum('bytes_received'),
        avg_bandwidth=Avg('duration')
    )
    
    # IP bazlı analiz (en çok trafik üreten)
    top_source_ips = total_traffic.values('source_ip').annotate(
        count=Count('id'),
        bytes_sent=Sum('bytes_sent'),
        bytes_received=Sum('bytes_received')
    )[:10]
    
    top_dest_ips = total_traffic.values('destination_ip').annotate(
        count=Count('id'),
        bytes_sent=Sum('bytes_sent'),
        bytes_received=Sum('bytes_received')
    )[:10]
    
    # Tehdit analizi
    suspicious_traffic = total_traffic.filter(is_suspicious=True)
    threat_levels = suspicious_traffic.values('threat_level').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Zaman bazlı analiz (son 24 saat, saatlik)
    hourly_stats = []
    for i in range(24):
        hour_start = start_time + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        
        hour_traffic = total_traffic.filter(
            timestamp__gte=hour_start,
            timestamp__lt=hour_end
        )
        
        hour_bytes = hour_traffic.aggregate(
            sent=Sum('bytes_sent'),
            received=Sum('bytes_received')
        )
        total_hour_bytes = (hour_bytes['sent'] or 0) + (hour_bytes['received'] or 0)
        
        hourly_stats.append({
            'hour': hour_start.strftime('%H:00'),
            'count': hour_traffic.count(),
            'total_bytes': total_hour_bytes,
            'suspicious': hour_traffic.filter(is_suspicious=True).count()
        })
    
    # Genel istatistikler
    total_bytes_agg = total_traffic.aggregate(
        sent=Sum('bytes_sent'),
        received=Sum('bytes_received')
    )
    total_bytes = (total_bytes_agg['sent'] or 0) + (total_bytes_agg['received'] or 0)
    
    stats = {
        'total_packets': total_traffic.count(),
        'total_bytes': total_bytes,
        'suspicious_count': suspicious_traffic.count(),
        'unique_ips': total_traffic.values('source_ip').distinct().count(),
        'avg_bandwidth': total_traffic.aggregate(Avg('duration'))['duration__avg'] or 0,
    }
    
    context = {
        'company': company,
        'stats': stats,
        'protocol_stats': protocol_stats,
        'top_source_ips': top_source_ips,
        'top_dest_ips': top_dest_ips,
        'threat_levels': threat_levels,
        'hourly_stats': hourly_stats,
        'start_time': start_time,
        'end_time': end_time,
    }
    
    return render(request, 'mirror_port/traffic_analysis.html', context)


@login_required
def traffic_detail(request, company_slug, traffic_id):
    """Trafik detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    context = {
        'company': company,
    }
    
    return render(request, 'mirror_port/traffic_detail.html', context)


@login_required
def devices_list(request, company_slug):
    """Cihaz listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Mevcut cihazları al
    devices = MirrorDevice.objects.filter(company=company).order_by('name')
    
    context = {
        'company': company,
        'devices': devices,
    }
    
    return render(request, 'mirror_port/devices_list.html', context)


@login_required
def device_add(request, company_slug):
    """Yeni mirror cihazı ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        device_type = request.POST.get('device_type')
        ip_address = request.POST.get('ip_address')
        mac_address = request.POST.get('mac_address', '')
        model = request.POST.get('model', '')
        manufacturer = request.POST.get('manufacturer', '')
        mirror_supported = request.POST.get('mirror_supported') == 'on'
        max_mirror_ports = int(request.POST.get('max_mirror_ports', 4))
        is_online = request.POST.get('is_online') == 'on'
        
        try:
            # Yeni cihaz oluştur
            device = MirrorDevice.objects.create(
                company=company,
                name=name,
                device_type=device_type,
                ip_address=ip_address,
                mac_address=mac_address,
                model=model,
                manufacturer=manufacturer,
                mirror_supported=mirror_supported,
                max_mirror_ports=max_mirror_ports,
                is_online=is_online
            )
            
            messages.success(request, f"Cihaz '{name}' başarıyla oluşturuldu.")
            return redirect('mirror_port:device_detail', company_slug=company.slug, device_id=device.id)
            
        except Exception as e:
            messages.error(request, f"Cihaz oluşturulamadı: {str(e)}")
    
    context = {
        'company': company,
    }
    
    return render(request, 'mirror_port/device_add.html', context)


@login_required
def device_detail(request, company_slug, device_id):
    """Cihaz detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Cihazı al
    device = get_object_or_404(MirrorDevice, id=device_id, company=company)
    
    context = {
        'company': company,
        'device': device,
    }
    
    return render(request, 'mirror_port/device_detail.html', context)


@login_required
def device_edit(request, company_slug, device_id):
    """Cihaz düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Cihazı al
    device = get_object_or_404(MirrorDevice, id=device_id, company=company)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        device_type = request.POST.get('device_type')
        ip_address = request.POST.get('ip_address')
        mac_address = request.POST.get('mac_address', '')
        model = request.POST.get('model', '')
        manufacturer = request.POST.get('manufacturer', '')
        mirror_supported = request.POST.get('mirror_supported') == 'on'
        max_mirror_ports = request.POST.get('max_mirror_ports')
        current_mirror_ports = request.POST.get('current_mirror_ports')
        is_online = request.POST.get('is_online') == 'on'
        
        if not name or not device_type or not ip_address:
            messages.error(request, 'Cihaz adı, tip ve IP adresi alanları zorunludur.')
        else:
            try:
                max_ports = int(max_mirror_ports) if max_mirror_ports else 4
                current_ports = int(current_mirror_ports) if current_mirror_ports else 0
                
                if max_ports < 1:
                    messages.error(request, 'Maksimum mirror port 1\'den büyük olmalıdır.')
                elif current_ports < 0:
                    messages.error(request, 'Mevcut mirror port negatif olamaz.')
                elif current_ports > max_ports:
                    messages.error(request, 'Mevcut mirror port maksimum port sayısından fazla olamaz.')
                else:
                    device.name = name
                    device.device_type = device_type
                    device.ip_address = ip_address
                    device.mac_address = mac_address
                    device.model = model
                    device.manufacturer = manufacturer
                    device.mirror_supported = mirror_supported
                    device.max_mirror_ports = max_ports
                    device.current_mirror_ports = current_ports
                    device.is_online = is_online
                    device.save()
                    
                    messages.success(request, f'Cihaz "{device.name}" başarıyla güncellendi.')
                    return redirect('mirror_port:devices_list', company.slug)
                    
            except ValueError:
                messages.error(request, 'Port sayıları geçerli sayılar olmalıdır.')
            except Exception as e:
                messages.error(request, f'Cihaz güncellenirken hata oluştu: {str(e)}')
    
    context = {
        'company': company,
        'device': device,
    }
    
    return render(request, 'mirror_port/device_edit.html', context)


@login_required
def device_delete(request, company_slug, device_id):
    """Cihaz silme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # Cihazı al
    device = get_object_or_404(MirrorDevice, id=device_id, company=company)
    
    if request.method == 'POST':
        try:
            device_name = device.name
            device.delete()
            messages.success(request, f'Cihaz "{device_name}" başarıyla silindi.')
            return redirect('mirror_port:devices_list', company.slug)
        except Exception as e:
            messages.error(request, f'Cihaz silinirken hata oluştu: {str(e)}')
            return redirect('mirror_port:devices_list', company.slug)
    
    context = {
        'company': company,
        'device': device,
    }
    
    return render(request, 'mirror_port/device_delete.html', context)


@login_required
def api_mirror_stats(request, company_slug):
    """Mirror istatistikleri API"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    return JsonResponse({
        'total_configurations': 0,
        'active_configurations': 0,
        'total_vlans': 0,
        'total_traffic': 0
    })
