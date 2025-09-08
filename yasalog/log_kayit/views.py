from django.shortcuts import render, redirect, get_object_or_404
from .forms import GirisForm
from .models import LogKayit, Company, CompanyUser
from .services import generate_log_hash, write_log_to_csv
from datetime import datetime
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.db.models import Q
from .exports import export_as_excel, export_as_pdf, export_as_zip
from django.core.paginator import Paginator
from django.db.models.functions import TruncHour
from django.db.models import Count
from django.contrib import messages
from django import forms
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

# Import user management views
from .views.user_management import (
    user_management_dashboard, add_user, edit_user, user_permissions,
    user_activity_logs, bulk_user_creation, toggle_user_status, delete_user
)

# Create your views here.

def dashboard_login_redirect(request):
    """Dashboard login sayfasına yönlendirme"""
    return redirect('log_kayit:yonetici_login')

# MAC adresi gerçek ortamda alınamaz, örnek olarak user-agent veya dummy değer kullanılabilir.
def get_mac_from_request(request):
    return request.META.get('HTTP_USER_AGENT', '00:00:00:00:00:00')

def giris_view(request, company_id=None, company_slug=None):
    # Eğer ne slug ne de id belirtilmemişse, bu genel bir giriştir.
    # Ziyaretçiyi özel link kullanması için bilgilendirme sayfasına yönlendir.
    if company_slug is None and company_id is None:
        return render(request, 'log_kayit/giris_landing.html')

    # Hem ID hem de slug ile firma bulma
    if company_slug:
        company_instance = get_object_or_404(Company, slug=company_slug)
    elif company_id:
        company_instance = get_object_or_404(Company, id=company_id)
    else:
        company_instance = None

    def _prepare_context(form):
        """Hazırlanan context'i döndürür."""
        company = form.company_instance if hasattr(form, 'company_instance') and form.company_instance else company_instance
        theme_color = company.theme_color if company else "#0d6efd"
        kvkk_text = company.kvkk_text if company else None
        login_info_text = company.login_info_text if company else None
        allow_foreigners = company.allow_foreigners if company else True
        return {
            'form': form, 
            'company': company, 
            'theme_color': theme_color, 
            'kvkk_text': kvkk_text, 
            'login_info_text': login_info_text, 
            'allow_foreigners': allow_foreigners
        }

    if request.method == 'POST':
        form = GirisForm(request.POST, user=request.user, company_instance=company_instance)
        if form.is_valid():
            log = form.save(commit=False)
            # Company'yi doğru şekilde ayarla
            if company_instance:
                log.company = company_instance
            elif form.cleaned_data.get('company'):
                log.company = form.cleaned_data['company']
            else:
                # Eğer hiçbiri yoksa, ilk firmayı al
                log.company = Company.objects.first()
            
            log.ip_adresi = request.META.get('REMOTE_ADDR', '0.0.0.0')
            log.mac_adresi = get_mac_from_request(request)
            
            # Önce kaydet ki giris_zamani oluşsun
            log.save()

            # Şimdi oluşan giris_zamani ile hash'i oluştur
            log.sha256_hash = generate_log_hash(
                log.tc_no, log.ad_soyad, log.telefon, log.ip_adresi, log.mac_adresi, log.giris_zamani
            )
            # Hash ile tekrar kaydet
            log.save()
            
            # write_log_to_csv(log) # İsteğe bağlı olarak açılabilir
            return render(request, 'log_kayit/tesekkur.html', {'company': log.company})
        else:
            # Geçersiz TC veya şüpheli girişte de log kaydı oluştur
            if hasattr(form, 'is_suspicious') and form.is_suspicious:
                suspicious_company = company_instance or form.cleaned_data.get('company') or Company.objects.first()
                LogKayit.objects.create(
                    company=suspicious_company,
                    tc_no=form.data.get('tc_no', ''),
                    pasaport_no=form.data.get('pasaport_no', ''),
                    kimlik_turu=form.data.get('kimlik_turu', 'TC'),
                    ad_soyad=form.data.get('ad_soyad', ''),
                    telefon=form.data.get('telefon', ''),
                    ip_adresi=request.META.get('REMOTE_ADDR', '0.0.0.0'),
                    mac_adresi=get_mac_from_request(request),
                    is_suspicious=True
                )
            context = _prepare_context(form)
            return render(request, 'log_kayit/giris.html', context)
    else:
        form = GirisForm(user=request.user, company_instance=company_instance)
    
    context = _prepare_context(form)
    return render(request, 'log_kayit/giris.html', context)

def _get_dashboard_statistics(logs, company):
    """Dashboard için temel istatistikleri ve kart verilerini hesaplar."""
    today = timezone.now().date()
    toplam_giris = logs.count()
    suspicious_logs = logs.filter(is_suspicious=True)
    
    today_logs = logs.filter(giris_zamani__date=today)
    
    most_active = logs.values('ad_soyad').annotate(count=Count('id')).order_by('-count').first()

    return {
        'toplam_giris': toplam_giris,
        'son_giris': logs.first(),
        'toplam_kullanici': CompanyUser.objects.filter(company=company).count(),
        'toplam_aktif_kullanici': CompanyUser.objects.filter(company=company, user__is_active=True).count(),
        'toplam_suspicious': suspicious_logs.count(),
        'today_total': today_logs.count(),
        'today_suspicious': today_logs.filter(is_suspicious=True).count(),
        'last_log_user': logs.first().ad_soyad if logs.first() else None,
        'last_log_time': logs.first().giris_zamani if logs.first() else None,
        'most_active_user': most_active['ad_soyad'] if most_active else None,
        'most_active_count': most_active['count'] if most_active else None,
    }

def _get_chart_data(logs):
    """Dashboard grafikleri için verileri hazırlar."""
    # Günlük girişler (son 30 gün)
    today = timezone.now().date()
    days = [today - timedelta(days=i) for i in range(29, -1, -1)]
    daily_counts = [logs.filter(giris_zamani__date=day).count() for day in days]

    # Saatlik girişler (son 24 saat)
    now = timezone.now()
    last_24_hours = [now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=i) for i in range(23, -1, -1)]
    hourly_qs = logs.filter(giris_zamani__gte=now - timedelta(hours=24))
    hour_map = {
        h['hour'].replace(tzinfo=None): h['count'] 
        for h in hourly_qs.annotate(hour=TruncHour('giris_zamani')).values('hour').annotate(count=Count('id'))
    }
    hourly_counts = [hour_map.get(h.replace(tzinfo=None), 0) for h in last_24_hours]
    
    # En çok giriş yapanlar
    top_users = logs.values('ad_soyad').annotate(count=Count('id')).order_by('-count')[:5]

    return {
        'days': [day.strftime('%d.%m') for day in days],
        'daily_counts': daily_counts,
        'hour_labels': [hour.strftime('%H:00') for hour in last_24_hours],
        'hourly_counts': hourly_counts,
        'top_users': top_users,
    }

@login_required
def company_dashboard(request, company_id=None, company_slug=None):
    # Özel durum: login slug'ı için yönlendirme
    if company_slug == 'login':
        return redirect('log_kayit:yonetici_login')
    
    # Hem ID hem de slug ile firma bulma
    if company_slug:
        company = get_object_or_404(Company, slug=company_slug)
    elif company_id:
        company = get_object_or_404(Company, id=company_id)
    else:
        return HttpResponseForbidden(_("Company not found."))
    
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden(_("You are not authorized to access this company's dashboard."))

    # İstatistikler için tüm logları al (filtresiz) ve ilişkili verileri önceden çek
    all_logs = LogKayit.objects.filter(company=company).select_related('company')

    # Filtreleme için kullanılacak temel log seti
    logs_to_filter = LogKayit.objects.filter(company=company)
    filter_params = {
        'tc_no': request.GET.get('tc_no', '').strip(),
        'ad_soyad': request.GET.get('ad_soyad', '').strip(),
        'date_start': request.GET.get('date_start', '').strip(),
        'date_end': request.GET.get('date_end', '').strip(),
    }
    if filter_params['tc_no']:
        logs_to_filter = logs_to_filter.filter(tc_no__icontains=filter_params['tc_no'])
    if filter_params['ad_soyad']:
        logs_to_filter = logs_to_filter.filter(ad_soyad__icontains=filter_params['ad_soyad'])
    if filter_params['date_start']:
        logs_to_filter = logs_to_filter.filter(giris_zamani__date__gte=filter_params['date_start'])
    if filter_params['date_end']:
        logs_to_filter = logs_to_filter.filter(giris_zamani__date__lte=filter_params['date_end'])

    # Logları geçerli ve şüpheli olarak ayır
    valid_logs = logs_to_filter.filter(is_suspicious=False)
    suspicious_logs = logs_to_filter.filter(is_suspicious=True)

    # Pagination
    paginator = Paginator(valid_logs.order_by('-giris_zamani'), 25)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    suspicious_paginator = Paginator(suspicious_logs.order_by('-giris_zamani'), 10)
    suspicious_page_obj = suspicious_paginator.get_page(request.GET.get('suspicious_page'))

    # Kullanıcı yetki ve bilgileri
    is_company_admin = CompanyUser.objects.filter(user=request.user, company=company, role='admin').exists() or request.user.is_superuser
    user_cu = CompanyUser.objects.filter(user=request.user, company=company).first()
    
    context = {
        'company': company,
        'logs': page_obj.object_list,
        'page_obj': page_obj,
        'suspicious_logs': suspicious_page_obj.object_list,
        'suspicious_page_obj': suspicious_page_obj,
        'filter_params': filter_params,
        'is_company_admin': is_company_admin,
        'user_last_login': request.user.last_login,
        'user_role': user_cu.get_role_display() if user_cu else (_("Superuser") if request.user.is_superuser else None),
        'theme_color': company.theme_color or "#0d6efd",
        'logo_url': company.logo.url if company.logo else None,
    }
    # İstatistikler tüm logları, grafikler ise sadece geçerli logları baz alsın
    context.update(_get_dashboard_statistics(all_logs, company))
    context.update(_get_chart_data(all_logs.filter(is_suspicious=False)))

    return render(request, 'log_kayit/dashboard.html', context)

def get_filtered_logs(request, company):
    logs = LogKayit.objects.filter(company=company).order_by('-giris_zamani')
    tc_no = request.GET.get('tc_no', '').strip()
    ad_soyad = request.GET.get('ad_soyad', '').strip()
    date_start = request.GET.get('date_start', '').strip()
    date_end = request.GET.get('date_end', '').strip()
    if tc_no:
        logs = logs.filter(tc_no__icontains=tc_no)
    if ad_soyad:
        logs = logs.filter(ad_soyad__icontains=ad_soyad)
    if date_start:
        logs = logs.filter(giris_zamani__date__gte=date_start)
    if date_end:
        logs = logs.filter(giris_zamani__date__lte=date_end)
    return logs

@login_required
def dashboard_export_excel(request, company_id=None, company_slug=None):
    # Hem ID hem de slug ile firma bulma
    if company_slug:
        company = get_object_or_404(Company, slug=company_slug)
    elif company_id:
        company = get_object_or_404(Company, id=company_id)
    else:
        return HttpResponseForbidden(_("Company not found."))
    
    if not CompanyUser.objects.filter(user=request.user, company=company).exists() and not request.user.is_superuser:
        return HttpResponseForbidden()
    logs = get_filtered_logs(request, company)
    output, error = export_as_excel(logs)
    if error:
        return HttpResponse(error, status=400)
    response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=loglar_{company.name}_{timezone.now().date()}.xlsx'
    return response

@login_required
def dashboard_export_pdf(request, company_id=None, company_slug=None):
    # Hem ID hem de slug ile firma bulma
    if company_slug:
        company = get_object_or_404(Company, slug=company_slug)
    elif company_id:
        company = get_object_or_404(Company, id=company_id)
    else:
        return HttpResponseForbidden(_("Company not found."))
    
    if not CompanyUser.objects.filter(user=request.user, company=company).exists() and not request.user.is_superuser:
        return HttpResponseForbidden()
    logs = get_filtered_logs(request, company)
    output, error = export_as_pdf(logs)
    if error:
        return HttpResponse(error, status=400)
    response = HttpResponse(output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=loglar_{company.name}_{timezone.now().date()}.pdf'
    return response

@login_required
def dashboard_export_zip(request, company_id=None, company_slug=None):
    # Hem ID hem de slug ile firma bulma
    if company_slug:
        company = get_object_or_404(Company, slug=company_slug)
    elif company_id:
        company = get_object_or_404(Company, id=company_id)
    else:
        return HttpResponseForbidden(_("Company not found."))
    
    if not CompanyUser.objects.filter(user=request.user, company=company).exists() and not request.user.is_superuser:
        return HttpResponseForbidden()
    logs = get_filtered_logs(request, company)
    output, error = export_as_zip(logs)
    if error:
        return HttpResponse(error, status=400)
    response = HttpResponse(output.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename=loglar_{company.name}_{timezone.now().date()}.zip'
    return response

@login_required
def company_user_panel(request):
    """
    Giriş yapan kullanıcıyı ait olduğu ilk firmanın paneline yönlendirir.
    Eğer kullanıcı süper kullanıcı ise veya hiçbir firmaya ait değilse,
    varsayılan (ilk) firmanın paneline yönlendirir.
    """
    user = request.user

    # Süper kullanıcılar tüm firmaları görebilir, varsayılan olarak ilk firmanın paneline gitsin.
    if user.is_superuser:
        first_company = Company.objects.first()
        if first_company and first_company.slug:
            return redirect('company_dashboard_slug', company_slug=first_company.slug)
        # Hiç firma yoksa veya slug yoksa admin paneline yönlendir
        return redirect('/admin/')

    # Normal kullanıcılar için
    company_user = CompanyUser.objects.filter(user=user).select_related('company').first()
    
    if company_user and company_user.company.slug:
        # Kullanıcının atandığı ilk firmanın paneline yönlendir
        return redirect('company_dashboard_slug', company_slug=company_user.company.slug)
    
    # Eğer kullanıcı bir firmaya atanmamışsa veya firmanın slug'ı yoksa,
    # bir hata mesajı göster ve giriş sayfasına geri gönder.
    messages.error(request, _("You are not associated with any company. Please contact an administrator."))
    return redirect('yonetici_login')

@login_required
def user_management_view(request):
    # Yetkilendirme ve firma belirleme mantığı (mevcut haliyle kalacak)
    user_company = None
    if request.user.is_superuser:
        all_companies = Company.objects.all()
        company_id = request.GET.get('company') or request.POST.get('company')
        user_company = Company.objects.filter(id=company_id).first() if company_id else all_companies.first()
    else:
        all_companies = None
        cu = CompanyUser.objects.filter(user=request.user, role='admin').select_related('company').first()
        if not cu:
            return HttpResponseForbidden(_("You are not authorized to manage users."))
        user_company = cu.company

    if not user_company:
        messages.error(request, _("No company found to manage."))
        return redirect('company_user_panel')

    # POST isteği ile kullanıcı durumunu değiştirme
    if request.method == 'POST':
        user_to_change_id = request.POST.get('user_id')
        action = request.POST.get('action')
        
        user_to_change_cu = get_object_or_404(CompanyUser, id=user_to_change_id, company=user_company)
        user_to_change = user_to_change_cu.user

        if action == 'toggle_active':
            # Kendi hesabını deaktive etmesini önle
            if user_to_change == request.user:
                messages.error(request, _("You cannot deactivate your own account."))
            else:
                user_to_change.is_active = not user_to_change.is_active
                user_to_change.save()
                messages.success(request, _("User '{username}' status has been updated.").format(username=user_to_change.username))
        
        elif action == 'change_role':
            new_role = request.POST.get('role')
            if new_role in [role[0] for role in CompanyUser.ROLE_CHOICES]:
                # Kendi rolünü değiştirmesini önle (eğer son admin ise)
                is_last_admin = (user_to_change_cu.role == 'admin' and 
                                 CompanyUser.objects.filter(company=user_company, role='admin').count() == 1)

                if user_to_change == request.user and is_last_admin:
                    messages.error(request, _("You cannot change your own role as you are the last administrator."))
                else:
                    user_to_change_cu.role = new_role
                    user_to_change_cu.save()
                    messages.success(request, _("User '{username}' role has been updated to '{role}'.").format(username=user_to_change.username, role=user_to_change_cu.get_role_display()))
            else:
                messages.error(request, _("Invalid role specified."))

        # İşlem sonrası aynı sayfaya yönlendirme
        redirect_url = reverse('user_management_view')
        return redirect(f'{redirect_url}?company={user_company.id}')

    # Mevcut kullanıcı listeleme mantığı (PERFORMANS İYİLEŞTİRMESİ)
    users = CompanyUser.objects.filter(company=user_company).select_related('user')

    # 1. Adım: Şirkete ait tüm log kayıtlarından isimlere göre gruplanmış sayımlar alınır.
    # Bu, veritabanına yapılan tek bir sorgudur.
    log_counts = LogKayit.objects.filter(company=user_company)\
                               .values('ad_soyad')\
                               .annotate(count=Count('id'))\
                               .order_by()

    # 2. Adım: Hızlı erişim için sayımları bir sözlük yapısına dönüştürülür.
    # Örn: {'Ahmet Yılmaz': 15, 'Ayşe Kaya': 22}
    log_counts_dict = {item['ad_soyad']: item['count'] for item in log_counts}

    # 3. Adım: Her kullanıcı için istatistikler, veritabanına tekrar sormadan oluşturulur.
    user_stats = {
        cu.id: {
            'last_login': cu.user.last_login,
            'log_count': log_counts_dict.get(cu.user.get_full_name(), 0),
            'is_active': cu.user.is_active,
        } for cu in users
    }

    return render(request, 'log_kayit/company_user_panel.html', {
        'users': users,
        'company': user_company,
        'all_companies': all_companies,
        'user_stats': user_stats,
    })

@login_required
def company_settings_panel(request):
    # Süperuser ise istediği firmanın ayarlarını görebilsin
    if request.user.is_superuser:
        from .models import Company
        all_companies = Company.objects.all()
        company_id = request.GET.get('company')
        if company_id:
            company = Company.objects.filter(id=company_id).first()
        else:
            company = all_companies.first()
    else:
        company_user = CompanyUser.objects.filter(user=request.user, role='admin').first()
        if not company_user:
            return HttpResponseForbidden(_("You are not authorized to view this page."))
        company = company_user.company
        all_companies = None
    if not company:
        messages.error(request, _("You are not assigned to any company. Cannot show settings."))
        return render(request, 'log_kayit/company_settings_panel.html', {'is_superuser': request.user.is_superuser})
    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, _('Settings saved successfully.'))
            return redirect('company_settings_panel')
        else:
            messages.error(request, _('Could not save settings. Please check the form.'))
    else:
        form = CompanySettingsForm(instance=company)
    return render(request, 'log_kayit/company_settings_panel.html', {'form': form, 'company': company, 'all_companies': all_companies})

class CompanySettingsForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ["name", "address", "contact_person", "phone", "logo", "kvkk_text", "login_info_text", "theme_color"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "contact_person": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "logo": forms.FileInput(attrs={"class": "form-control"}),
            "kvkk_text": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
            "login_info_text": forms.TextInput(attrs={"class": "form-control"}),
            "theme_color": forms.TextInput(attrs={"type": "color", "class": "form-control form-control-color"}),
        }
