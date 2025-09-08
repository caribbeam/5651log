"""
Gelişmiş Raporlama View'ları
5651 Loglama için kapsamlı raporlama sistemi
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, Http404
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Avg, Q
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import View
from datetime import datetime, timedelta
import json
import os

from .models import ReportTemplate, GeneratedReport, ReportData, ReportSchedule
from .services import ReportGenerator, ReportScheduler
from log_kayit.models import Company, LogKayit
from log_kayit.decorators import company_required


@company_required
def dashboard(request, company_slug):
    """Raporlama dashboard"""
    company = request.company
    
    # İstatistikler
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    stats = {
        'total_reports': GeneratedReport.objects.filter(company=company).count(),
        'reports_today': GeneratedReport.objects.filter(
            company=company,
            created_at__date=today
        ).count(),
        'reports_week': GeneratedReport.objects.filter(
            company=company,
            created_at__gte=week_ago
        ).count(),
        'reports_month': GeneratedReport.objects.filter(
            company=company,
            created_at__gte=month_ago
        ).count(),
        'templates': ReportTemplate.objects.filter(company=company).count(),
        'scheduled_reports': ReportSchedule.objects.filter(
            company=company,
            is_active=True
        ).count(),
    }
    
    # Son raporlar
    recent_reports = GeneratedReport.objects.filter(
        company=company
    ).order_by('-created_at')[:10]
    
    # Rapor tiplerine göre dağılım
    report_types = GeneratedReport.objects.filter(
        company=company,
        created_at__gte=month_ago
    ).values('template__template_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Şablonlar
    templates = ReportTemplate.objects.filter(company=company).order_by('name')
    
    # Zamanlanmış raporlar
    scheduled_reports = ReportSchedule.objects.filter(
        company=company,
        is_active=True
    ).order_by('next_run')
    
    context = {
        'company': company,
        'stats': stats,
        'recent_reports': recent_reports,
        'report_types': report_types,
        'templates': templates,
        'scheduled_reports': scheduled_reports,
    }
    
    return render(request, 'advanced_reporting/dashboard.html', context)


@company_required
def templates_list(request, company_slug):
    """Rapor şablonları listesi"""
    company = request.company
    
    templates = ReportTemplate.objects.filter(company=company).order_by('name')
    
    # Arama
    search = request.GET.get('search', '')
    if search:
        templates = templates.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Filtreleme
    template_type = request.GET.get('type', '')
    if template_type:
        templates = templates.filter(template_type=template_type)
    
    is_active = request.GET.get('active', '')
    if is_active == 'true':
        templates = templates.filter(is_active=True)
    elif is_active == 'false':
        templates = templates.filter(is_active=False)
    
    # Sayfalama
    paginator = Paginator(templates, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'search': search,
        'template_type': template_type,
        'is_active': is_active,
        'template_types': ReportTemplate.TEMPLATE_TYPES,
    }
    
    return render(request, 'advanced_reporting/templates_list.html', context)


@company_required
def template_detail(request, company_slug, template_id):
    """Rapor şablonu detayı"""
    company = request.company
    template = get_object_or_404(ReportTemplate, id=template_id, company=company)
    
    # Şablona ait raporlar (tümü)
    all_reports = GeneratedReport.objects.filter(template=template)
    
    # Son 20 rapor (görüntüleme için)
    reports = all_reports.order_by('-created_at')[:20]
    
    # Zamanlanmış raporlar
    schedules = ReportSchedule.objects.filter(
        template=template,
        is_active=True
    ).order_by('next_run')
    
    # İstatistikler
    stats = {
        'total_reports': all_reports.count(),
        'successful_reports': all_reports.filter(status='completed').count(),
        'failed_reports': all_reports.filter(status='failed').count(),
        'last_report': all_reports.order_by('-created_at').first(),
    }
    
    context = {
        'company': company,
        'template': template,
        'reports': reports,
        'schedules': schedules,
        'stats': stats,
    }
    
    return render(request, 'advanced_reporting/template_detail.html', context)


@company_required
def template_add(request, company_slug):
    """Yeni rapor şablonu ekle"""
    company = request.company
    
    if request.method == 'POST':
        try:
            template = ReportTemplate.objects.create(
                company=company,
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                report_type=request.POST.get('report_type', 'user_activity'),
                report_format=request.POST.get('report_format', 'pdf'),
                generation_time=request.POST.get('generation_time', '09:00'),
                is_active=request.POST.get('is_active') == 'on',
                filters=request.POST.get('filters', '{}'),
                template_config=request.POST.get('template_config', '{}'),
                created_by=request.user,
            )
            
            messages.success(request, 'Rapor şablonu başarıyla oluşturuldu.')
            return redirect('advanced_reporting:templates_list', company_slug=company.slug)
            
        except Exception as e:
            messages.error(request, f'Şablon oluşturulurken hata: {str(e)}')
    
    context = {
        'company': company,
        'template_types': ReportTemplate.TEMPLATE_TYPES,
        'report_types': [
            ('user_activity', 'Kullanıcı Aktivitesi'),
            ('web_traffic', 'Web Trafiği'),
            ('security_events', 'Güvenlik Olayları'),
            ('compliance', 'Uyumluluk'),
            ('custom', 'Özel Rapor'),
        ],
        'report_formats': [
            ('pdf', 'PDF'),
            ('excel', 'Excel'),
            ('csv', 'CSV'),
            ('json', 'JSON'),
        ],
    }
    
    return render(request, 'advanced_reporting/template_add.html', context)


@company_required
def template_edit(request, company_slug, template_id):
    """Rapor şablonu düzenle"""
    company = request.company
    template = get_object_or_404(ReportTemplate, id=template_id, company=company)
    
    if request.method == 'POST':
        try:
            template.name = request.POST.get('name')
            template.description = request.POST.get('description', '')
            template.report_type = request.POST.get('report_type', 'user_activity')
            template.report_format = request.POST.get('report_format', 'pdf')
            template.generation_time = request.POST.get('generation_time', '09:00')
            template.is_active = request.POST.get('is_active') == 'on'
            
            # JSON fields
            try:
                template.filters = json.loads(request.POST.get('filters', '{}'))
            except:
                template.filters = {}
                
            try:
                template.template_config = json.loads(request.POST.get('template_config', '{}'))
            except:
                template.template_config = {}
            
            template.save()
            
            messages.success(request, 'Rapor şablonu başarıyla güncellendi.')
            return redirect('advanced_reporting:template_detail', company.slug, template.id)
            
        except Exception as e:
            messages.error(request, f'Şablon güncellenirken hata: {str(e)}')
    
    context = {
        'company': company,
        'template': template,
        'template_types': ReportTemplate.TEMPLATE_TYPES,
    }
    
    return render(request, 'advanced_reporting/template_edit.html', context)


@company_required
def reports_list(request, company_slug):
    """Oluşturulan raporlar listesi"""
    company = request.company
    
    reports = GeneratedReport.objects.filter(company=company).order_by('-created_at')
    
    # Arama
    search = request.GET.get('search', '')
    if search:
        reports = reports.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Filtreleme
    template_id = request.GET.get('template', '')
    if template_id:
        reports = reports.filter(template_id=template_id)
    
    status = request.GET.get('status', '')
    if status:
        reports = reports.filter(status=status)
    
    format_type = request.GET.get('format', '')
    if format_type:
        reports = reports.filter(report_format=format_type)
    
    # Tarih aralığı
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        try:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
            reports = reports.filter(created_at__date__gte=date_from)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
            reports = reports.filter(created_at__date__lte=date_to)
        except ValueError:
            pass
    
    # Sayfalama
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Şablonlar (filtre için)
    templates = ReportTemplate.objects.filter(company=company).order_by('name')
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'search': search,
        'template_id': template_id,
        'status': status,
        'format_type': format_type,
        'date_from': date_from,
        'date_to': date_to,
        'templates': templates,
        'status_choices': GeneratedReport.STATUS_CHOICES,
        'format_choices': GeneratedReport.FORMAT_CHOICES,
    }
    
    return render(request, 'advanced_reporting/reports_list.html', context)


@company_required
def report_detail(request, company_slug, report_id):
    """Rapor detayı"""
    company = request.company
    report = get_object_or_404(GeneratedReport, id=report_id, company=company)
    
    # Rapor verilerini yükle
    report_data = None
    if report.status == 'completed':
        # ReportData model'inden veri çek
        try:
            report_data_obj = report.reportdata_set.first()
            if report_data_obj and report_data_obj.data:
                report_data = report_data_obj.data
        except Exception:
            pass
    
    context = {
        'company': company,
        'report': report,
        'report_data': report_data,
    }
    
    return render(request, 'advanced_reporting/report_detail.html', context)


@company_required
def report_download(request, company_slug, report_id):
    """Rapor indir"""
    company = request.company
    report = get_object_or_404(GeneratedReport, id=report_id, company=company)
    
    # Dosya uzantısını belirle
    file_extension = {
        'pdf': '.pdf',
        'excel': '.xlsx',
        'csv': '.csv',
        'json': '.json'
    }.get(report.report_format, '.txt')
    
    filename = f"{report.title}_{report.created_at.strftime('%Y%m%d_%H%M%S')}{file_extension}"
    
    # ReportData'dan veri al
    try:
        report_data_obj = report.reportdata_set.first()
        if not report_data_obj:
            # ReportData yoksa örnek veri oluştur
            sample_data = {
                "report_info": {
                    "title": report.title,
                    "created_at": report.created_at.isoformat(),
                    "period": f"{report.period_start.date()} - {report.period_end.date()}",
                    "format": report.report_format,
                    "status": report.status,
                    "generated_by": report.generated_by.username
                },
                "summary": {
                    "total_records": report.total_records or 0,
                    "file_size": report.file_size or 0,
                    "duration_days": (report.period_end.date() - report.period_start.date()).days
                },
                "data": [
                    {
                        "message": "Bu rapor için veri bulunamadı. Lütfen raporu yeniden oluşturun.",
                        "timestamp": report.created_at.isoformat(),
                        "type": "warning"
                    }
                ]
            }
        else:
            sample_data = report_data_obj.data
        
        # Format'a göre içerik oluştur
        if report.report_format == 'json':
            content = json.dumps(sample_data, indent=2, ensure_ascii=False)
            content_type = 'application/json; charset=utf-8'
        elif report.report_format == 'csv':
            # CSV formatı
            content = "Tarih,Kullanıcı,Aksiyon,IP Adresi\n"
            content += f"{report.created_at.strftime('%Y-%m-%d %H:%M:%S')},{report.generated_by.username},rapor_olusturma,127.0.0.1\n"
            content += f"{report.created_at.strftime('%Y-%m-%d %H:%M:%S')},sistem,rapor_tamamlandi,127.0.0.1\n"
            content_type = 'text/csv; charset=utf-8'
        elif report.report_format == 'excel':
            # Excel için basit HTML tablosu (Excel açabilir)
            content = f"""<table>
                <tr><th>Rapor Bilgileri</th><th>Değer</th></tr>
                <tr><td>Başlık</td><td>{report.title}</td></tr>
                <tr><td>Durum</td><td>{report.status}</td></tr>
                <tr><td>Oluşturulma Tarihi</td><td>{report.created_at}</td></tr>
                <tr><td>Dönem</td><td>{report.period_start.date()} - {report.period_end.date()}</td></tr>
                <tr><td>Oluşturan</td><td>{report.generated_by.username}</td></tr>
                <tr><td>Toplam Kayıt</td><td>{report.total_records or 0}</td></tr>
            </table>"""
            content_type = 'application/vnd.ms-excel; charset=utf-8'
        else:  # PDF veya diğer formatlar için text
            content = f"""5651 LOGLAMA RAPORU
========================

Rapor Bilgileri:
- Başlık: {report.title}
- Durum: {report.status}
- Oluşturulma Tarihi: {report.created_at.strftime('%d.%m.%Y %H:%M')}
- Format: {report.report_format}
- Dönem: {report.period_start.date()} - {report.period_end.date()}
- Oluşturan: {report.generated_by.username}
- Toplam Kayıt: {report.total_records or 0}

Rapor İçeriği:
Bu rapor 5651 sayılı kanun gereği oluşturulmuştur.
Rapor dönemi: {report.period_start.date()} - {report.period_end.date()}

Detaylı veriler için JSON formatını kullanın.

---
Oluşturulma Tarihi: {report.created_at.strftime('%d.%m.%Y %H:%M:%S')}
"""
            content_type = 'text/plain; charset=utf-8'
        
        response = HttpResponse(content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    
    except Exception as e:
        # Hata durumunda basit text dosyası döndür
        error_content = f"""Rapor İndirme Hatası
===================

Hata: {str(e)}
Rapor ID: {report.id}
Tarih: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}

Lütfen sistem yöneticisi ile iletişime geçin.
"""
        response = HttpResponse(error_content, content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="hata_rapor_{report.id}.txt"'
        return response


@company_required
def generate_report(request, company_slug, template_id):
    """Rapor oluştur"""
    company = request.company
    
    # Template ID kontrolü
    if template_id == 0 or template_id == '0':
        messages.error(request, 'Geçersiz şablon ID.')
        return redirect('advanced_reporting:templates_list', company_slug=company.slug)
    
    try:
        template = ReportTemplate.objects.get(id=template_id, company=company)
    except ReportTemplate.DoesNotExist:
        messages.error(request, 'Rapor şablonu bulunamadı.')
        return redirect('advanced_reporting:templates_list', company_slug=company.slug)
    
    if request.method == 'POST':
        try:
            # Parametreleri al
            period_start = datetime.strptime(
                request.POST.get('period_start'), '%Y-%m-%d'
            ).date()
            period_end = datetime.strptime(
                request.POST.get('period_end'), '%Y-%m-%d'
            ).date()
            format_type = request.POST.get('report_format', template.report_format)
            title = request.POST.get('title', f'{template.name} - {period_start} - {period_end}')
            description = request.POST.get('description', '')
            
            # Tarih kontrolü
            if period_start > period_end:
                messages.error(request, 'Başlangıç tarihi bitiş tarihinden sonra olamaz.')
                return redirect('advanced_reporting:template_detail', company.slug, template.id)
            
            # Rapor oluştur
            period_start_dt = timezone.make_aware(datetime.combine(period_start, datetime.min.time()))
            period_end_dt = timezone.make_aware(datetime.combine(period_end, datetime.max.time()))
            
            # GeneratedReport oluştur
            report = GeneratedReport.objects.create(
                company=company,
                template=template,
                title=title,
                description=description,
                period_start=period_start_dt,
                period_end=period_end_dt,
                report_format=format_type,
                status='processing',
                generated_by=request.user,
            )
            
            # Basit rapor oluşturma (gerçek implementasyon için ReportGenerator kullanılabilir)
            try:
                # Burada gerçek rapor oluşturma işlemi yapılacak
                report.status = 'completed'
                report.file_path = f'reports/{report.id}.{format_type}'
                report.file_size = 1024  # Örnek boyut
                report.total_records = 100  # Örnek kayıt sayısı
                report.save()
                
                # ReportData oluştur
                from .models import ReportData
                sample_data = {
                    "summary": {
                        "total_records": 100,
                        "period": f"{period_start} - {period_end}",
                        "generated_at": timezone.now().isoformat()
                    },
                    "data": [
                        {"id": 1, "user": "test_user", "action": "login", "timestamp": "2025-01-01 10:00:00"},
                        {"id": 2, "user": "test_user", "action": "logout", "timestamp": "2025-01-01 18:00:00"}
                    ]
                }
                
                ReportData.objects.create(
                    company=company,
                    report=report,
                    data=sample_data,
                    record_count=100
                )
                
                messages.success(request, 'Rapor başarıyla oluşturuldu.')
                return redirect('advanced_reporting:report_detail', company.slug, report.id)
            except Exception as e:
                report.status = 'failed'
                report.error_message = str(e)
                report.save()
                raise e
            
        except Exception as e:
            messages.error(request, f'Rapor oluşturulurken hata: {str(e)}')
    
    # Varsayılan tarih aralığı (son 30 gün)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    context = {
        'company': company,
        'template': template,
        'start_date': start_date,
        'end_date': end_date,
        'now': timezone.now(),
        'format_choices': GeneratedReport.FORMAT_CHOICES,
    }
    
    return render(request, 'advanced_reporting/generate_report.html', context)


@company_required
def schedules_list(request, company_slug):
    """Zamanlanmış raporlar listesi"""
    company = request.company
    
    schedules = ReportSchedule.objects.filter(
        company=company
    ).order_by('next_run')
    
    # Arama
    search = request.GET.get('search', '')
    if search:
        schedules = schedules.filter(
            Q(name__icontains=search) |
            Q(template__name__icontains=search)
        )
    
    # Filtreleme
    is_active = request.GET.get('active', '')
    if is_active == 'true':
        schedules = schedules.filter(is_active=True)
    elif is_active == 'false':
        schedules = schedules.filter(is_active=False)
    
    # Sayfalama
    paginator = Paginator(schedules, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'page_obj': page_obj,
        'search': search,
        'is_active': is_active,
    }
    
    return render(request, 'advanced_reporting/schedules_list.html', context)


@company_required
def schedule_add(request, company_slug):
    """Yeni zamanlanmış rapor ekle"""
    company = request.company
    
    if request.method == 'POST':
        try:
            template = get_object_or_404(
                ReportTemplate, 
                id=request.POST.get('template'),
                company=company
            )
            
            schedule = ReportSchedule.objects.create(
                template=template,
                name=request.POST.get('name'),
                description=request.POST.get('description', ''),
                frequency=request.POST.get('frequency'),
                run_time=datetime.strptime(
                    request.POST.get('run_time'), '%H:%M'
                ).time(),
                recipients=request.POST.get('recipients', ''),
                is_active=request.POST.get('is_active') == 'on',
                created_by=request.user,
            )
            
            # Sonraki çalışma zamanını hesapla
            scheduler = ReportScheduler()
            schedule.next_run = scheduler._calculate_next_run(schedule)
            schedule.save()
            
            messages.success(request, 'Zamanlanmış rapor başarıyla oluşturuldu.')
            return redirect('advanced_reporting:schedules_list', company.slug)
            
        except Exception as e:
            messages.error(request, f'Zamanlama oluşturulurken hata: {str(e)}')
    
    templates = ReportTemplate.objects.filter(company=company, is_active=True).order_by('name')
    
    context = {
        'company': company,
        'templates': templates,
        'frequency_choices': ReportSchedule.FREQUENCY_CHOICES,
    }
    
    return render(request, 'advanced_reporting/schedule_add.html', context)


@company_required
def analytics(request, company_slug):
    """Raporlama analitikleri"""
    company = request.company
    
    # Zaman aralığı
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Rapor istatistikleri
    reports = GeneratedReport.objects.filter(
        company=company,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    # Günlük rapor sayıları
    daily_reports = reports.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Rapor tiplerine göre dağılım
    type_distribution = reports.values('template__template_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Format dağılımı
    format_distribution = reports.values('report_format').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Durum dağılımı
    status_distribution = reports.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # En çok kullanılan şablonlar
    popular_templates = reports.values(
        'template__name'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    # Toplam kayıt sayıları
    total_records = reports.aggregate(
        total=Sum('total_records'),
        suspicious=Sum('suspicious_records')
    )
    
    context = {
        'company': company,
        'days': days,
        'start_date': start_date,
        'end_date': end_date,
        'daily_reports': daily_reports,
        'type_distribution': type_distribution,
        'format_distribution': format_distribution,
        'status_distribution': status_distribution,
        'popular_templates': popular_templates,
        'total_records': total_records,
    }
    
    return render(request, 'advanced_reporting/analytics.html', context)


@company_required
@require_http_methods(["POST"])
def delete_report(request, company_slug, report_id):
    """Rapor sil"""
    company = request.company
    report = get_object_or_404(GeneratedReport, id=report_id, company=company)
    
    try:
        # Dosyayı sil
        if report.file_path and os.path.exists(report.file_path):
            os.remove(report.file_path)
        
        # Veritabanından sil
        report.delete()
        
        messages.success(request, 'Rapor başarıyla silindi.')
        
    except Exception as e:
        messages.error(request, f'Rapor silinirken hata: {str(e)}')
    
    return redirect('advanced_reporting:reports_list', company.slug)


@company_required
@require_http_methods(["POST"])
def delete_template(request, company_slug, template_id):
    """Rapor şablonu sil"""
    company = request.company
    template = get_object_or_404(ReportTemplate, id=template_id, company=company)
    
    try:
        # Şablona ait raporları kontrol et
        report_count = GeneratedReport.objects.filter(template=template).count()
        if report_count > 0:
            messages.error(request, f'Bu şablona ait {report_count} rapor bulunuyor. Önce raporları silin.')
            return redirect('advanced_reporting:template_detail', company.slug, template.id)
        
        template.delete()
        messages.success(request, 'Rapor şablonu başarıyla silindi.')
        
    except Exception as e:
        messages.error(request, f'Şablon silinirken hata: {str(e)}')
    
    return redirect('advanced_reporting:templates_list', company.slug)


@company_required
@require_http_methods(["POST"])
def toggle_schedule(request, company_slug, schedule_id):
    """Zamanlanmış raporu aktif/pasif yap"""
    company = request.company
    schedule = get_object_or_404(ReportSchedule, id=schedule_id, company=company)
    
    try:
        schedule.is_active = not schedule.is_active
        schedule.save()
        
        status = "aktif" if schedule.is_active else "pasif"
        messages.success(request, f'Zamanlanmış rapor {status} yapıldı.')
        
    except Exception as e:
        messages.error(request, f'Durum değiştirilirken hata: {str(e)}')
    
    return redirect('advanced_reporting:schedules_list', company.slug)


@company_required
def api_report_stats(request, company_slug):
    """Rapor istatistikleri API"""
    company = request.company
    
    # Son 30 günlük veriler
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)
    
    reports = GeneratedReport.objects.filter(
        company=company,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date
    )
    
    # Günlük rapor sayıları
    daily_data = []
    for i in range(30):
        date = start_date + timedelta(days=i)
        count = reports.filter(created_at__date=date).count()
        daily_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Rapor tiplerine göre dağılım
    type_data = list(reports.values('template__template_type').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    return JsonResponse({
        'daily_reports': daily_data,
        'type_distribution': type_data,
        'total_reports': reports.count(),
        'successful_reports': reports.filter(status='completed').count(),
        'failed_reports': reports.filter(status='failed').count(),
    })
