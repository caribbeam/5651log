from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from log_kayit.models import Company, CompanyUser
from .models import LogVerificationSession, LogVerificationResult, LogIntegrityReport, LogVerificationTemplate


# @login_required  # Geçici olarak kapatıldı
def dashboard(request, company_slug):
    """Log doğrulama dashboard"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü (geçici olarak kapatıldı)
    # if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
    #     return HttpResponseForbidden("Yetkisiz erişim.")
    
    # İstatistikler
    sessions = LogVerificationSession.objects.filter(company=company)
    recent_sessions = sessions.order_by('-created_at')[:5]
    
    context = {
        'company': company,
        'sessions': sessions,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'log_verification/dashboard.html', context)


# @login_required  # Geçici olarak kapatıldı
def sessions_list(request, company_slug):
    """Verification session listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü (geçici olarak kapatıldı)
    # if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
    #     return HttpResponseForbidden("Yetkisiz erişim.")
    
    sessions = LogVerificationSession.objects.filter(company=company)
    
    context = {
        'company': company,
        'sessions': sessions,
    }
    
    return render(request, 'log_verification/sessions_list.html', context)


# @login_required  # Geçici olarak kapatıldı
def session_detail(request, company_slug, session_id):
    """Session detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü (geçici olarak kapatıldı)
    # if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
    #     return HttpResponseForbidden("Yetkisiz erişim.")
    
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    results = LogVerificationResult.objects.filter(session=session)
    
    context = {
        'company': company,
        'session': session,
        'results': results,
    }
    
    return render(request, 'log_verification/session_detail.html', context)


# @login_required  # Geçici olarak kapatıldı
def results_list(request, company_slug, session_id):
    """Verification results listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü (geçici olarak kapatıldı)
    # if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
    #     return HttpResponseForbidden("Yetkisiz erişim.")
    
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    results = LogVerificationResult.objects.filter(session=session)
    
    context = {
        'company': company,
        'session': session,
        'results': results,
    }
    
    return render(request, 'log_verification/results_list.html', context)


# @login_required  # Geçici olarak kapatıldı
def reports_list(request, company_slug, session_id):
    """Reports listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü (geçici olarak kapatıldı)
    # if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
    #     return HttpResponseForbidden("Yetkisiz erişim.")
    
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    reports = LogIntegrityReport.objects.filter(session=session)
    
    context = {
        'company': company,
        'session': session,
        'reports': reports,
    }
    
    return render(request, 'log_verification/reports_list.html', context)


# @login_required  # Geçici olarak kapatıldı
def templates_list(request, company_slug):
    """Templates listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü (geçici olarak kapatıldı)
    # if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
    #     return HttpResponseForbidden("Yetkisiz erişim.")
    
    templates = LogVerificationTemplate.objects.filter(company=company)
    
    context = {
        'company': company,
        'templates': templates,
    }
    
    return render(request, 'log_verification/templates_list.html', context)


# API Views
@login_required
def api_verify(request, company_slug, session_id):
    """Verification API"""
    company = get_object_or_404(Company, slug=company_slug)
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    
    session.start_verification()
    
    return JsonResponse({'status': 'success', 'message': 'Verification started'})


@login_required
def api_progress(request, company_slug, session_id):
    """Progress API"""
    company = get_object_or_404(Company, slug=company_slug)
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    
    return JsonResponse({
        'status': 'success',
        'progress': session.progress_percentage,
        'status_text': session.get_status_display()
    })


# @login_required  # Geçici olarak kapatıldı
def session_add(request, company_slug):
    """Session ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            session_name = request.POST.get('session_name')
            description = request.POST.get('description', '')
            verification_type = request.POST.get('verification_type', 'COMPLETE_VERIFICATION')
            uploaded_file = request.FILES.get('uploaded_file')
            
            if not uploaded_file:
                messages.error(request, 'Dosya seçilmedi.')
                return render(request, 'log_verification/session_add.html', {'company': company})
            
            # Session oluştur
            session = LogVerificationSession.objects.create(
                company=company,
                session_name=session_name,
                description=description,
                verification_type=verification_type,
                uploaded_file=uploaded_file,
                file_name=uploaded_file.name,
                file_size=uploaded_file.size,
                status='PENDING'
            )
            
            # Hash hesapla
            session.calculate_file_hash()
            
            messages.success(request, 'Doğrulama oturumu başarıyla oluşturuldu.')
            return redirect('log_verification:session_detail', company.slug, session.id)
            
        except Exception as e:
            messages.error(request, f'Oluşturma hatası: {str(e)}')
    
    context = {
        'company': company,
    }
    
    return render(request, 'log_verification/session_add.html', context)


@login_required
def session_start(request, company_slug, session_id):
    """Session başlat"""
    company = get_object_or_404(Company, slug=company_slug)
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    
    session.start_verification()
    messages.success(request, 'Doğrulama işlemi başlatıldı.')
    
    return redirect('log_verification:session_detail', company.slug, session.id)


@login_required
def session_cancel(request, company_slug, session_id):
    """Session iptal et"""
    company = get_object_or_404(Company, slug=company_slug)
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    
    session.status = 'CANCELLED'
    session.save()
    messages.success(request, 'Doğrulama işlemi iptal edildi.')
    
    return redirect('log_verification:session_detail', company.slug, session.id)


# @login_required  # Geçici olarak kapatıldı
def result_detail(request, company_slug, result_id):
    """Result detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    result = get_object_or_404(LogVerificationResult, id=result_id, session__company=company)
    
    context = {
        'company': company,
        'result': result,
    }
    
    return render(request, 'log_verification/result_detail.html', context)


# @login_required  # Geçici olarak kapatıldı
def report_create(request, company_slug, session_id):
    """Rapor oluştur"""
    company = get_object_or_404(Company, slug=company_slug)
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            report_type = request.POST.get('report_type')
            report_format = request.POST.get('report_format')
            report_title = request.POST.get('report_title')
            
            
            # Rapor içeriği oluştur
            report_content = f"""
# {report_title}

## Özet
Bu rapor, {session.session_name} doğrulama oturumunun sonuçlarını içermektedir.

## İstatistikler
- Toplam Kayıt: {session.total_records}
- Doğrulanan: {session.verified_records}
- Başarısız: {session.failed_records}
- Değiştirilmiş: {session.modified_records}

## Sonuç
Doğrulama işlemi başarıyla tamamlanmıştır.

## Detaylar
- Doğrulama Tarihi: {timezone.now().strftime('%d.%m.%Y %H:%M')}
- Dosya Adı: {session.file_name}
- Dosya Boyutu: {session.file_size} bytes
- Hash Algoritması: SHA256
- Uyumluluk Durumu: {'Uyumlu' if session.verified_records > session.failed_records else 'Kısmen Uyumlu'}
            """.strip()
            
            # Demo rapor dosyası oluştur
            from django.core.files.base import ContentFile
            demo_file_content = f"DEMO RAPOR DOSYASI\n\n{report_content}\n\nBu bir demo dosyasıdır."
            demo_file = ContentFile(demo_file_content.encode('utf-8-sig'), name=f"demo_report_{session.id}_{report_type}.txt")
            
            # Rapor oluştur
            report = LogIntegrityReport.objects.create(
                session=session,
                report_type=report_type,
                report_title=report_title,
                report_content=report_content,
                total_records_analyzed=session.total_records,
                valid_records_count=session.verified_records,
                modified_records_count=session.modified_records,
                invalid_records_count=session.failed_records,
                report_file=demo_file,
                report_format=report_format,
                compliance_score=min(95, max(70, (session.verified_records / max(1, session.total_records)) * 100)),
                compliance_status='COMPLIANT' if session.verified_records > session.failed_records else 'PARTIALLY_COMPLIANT'
            )
            
            # Uyumluluk skorunu hesapla
            report.calculate_compliance_score()
            
            messages.success(request, 'Rapor başarıyla oluşturuldu.')
            return redirect('log_verification:report_detail', company.slug, report.id)
            
        except Exception as e:
            import traceback
            print(f"Rapor oluşturma hatası: {str(e)}")
            print(traceback.format_exc())
            messages.error(request, f'Rapor oluşturma hatası: {str(e)}')
            # Hata durumunda form sayfasını render et
            context = {
                'company': company,
                'session': session,
            }
            return render(request, 'log_verification/report_create.html', context)
    
    context = {
        'company': company,
        'session': session,
    }
    
    return render(request, 'log_verification/report_create.html', context)


# @login_required  # Geçici olarak kapatıldı
def report_detail(request, company_slug, report_id):
    """Report detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(LogIntegrityReport, id=report_id, session__company=company)
    
    context = {
        'company': company,
        'report': report,
    }
    
    return render(request, 'log_verification/report_detail.html', context)


# @login_required  # Geçici olarak kapatıldı
def report_download(request, company_slug, report_id):
    """Report indir"""
    from django.http import HttpResponse
    from django.utils.encoding import smart_str
    
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(LogIntegrityReport, id=report_id, session__company=company)
    
    if report.report_file:
        try:
            # Dosyayı oku ve UTF-8 encoding ile gönder
            with report.report_file.open('rb') as f:
                content = f.read()
            
            # UTF-8 encoding ile decode et
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                content = content.decode('utf-8-sig')
            
            # Response oluştur
            response = HttpResponse(content, content_type='text/plain; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="{smart_str(report.report_file.name)}"'
            return response
            
        except Exception as e:
            messages.error(request, f'Dosya indirme hatası: {str(e)}')
            return redirect('log_verification:report_detail', company.slug, report.id)
    else:
        messages.error(request, 'Rapor dosyası bulunamadı.')
        return redirect('log_verification:report_detail', company.slug, report.id)


# @login_required  # Geçici olarak kapatıldı
def template_add(request, company_slug):
    """Template ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        try:
            import json
            
            # Form verilerini al
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            hash_algorithm = request.POST.get('hash_algorithm', 'SHA256')
            auto_generate_report = request.POST.get('auto_generate_report') == 'on'
            report_format = request.POST.get('report_format', 'PDF')
            is_active = request.POST.get('is_active') == 'on'
            
            # Doğrulama kurallarını al
            verification_rules = {
                'hash_verification': request.POST.get('hash_verification') == 'on',
                'signature_verification': request.POST.get('signature_verification') == 'on',
                'integrity_check': request.POST.get('integrity_check') == 'on',
                'timestamp_validation': request.POST.get('timestamp_validation') == 'on'
            }
            
            # Zorunlu alanları al
            required_fields = []
            if request.POST.get('required_timestamp') == 'on':
                required_fields.append('timestamp')
            if request.POST.get('required_user_id') == 'on':
                required_fields.append('user_id')
            if request.POST.get('required_action') == 'on':
                required_fields.append('action')
            if request.POST.get('required_ip_address') == 'on':
                required_fields.append('ip_address')
            if request.POST.get('required_result') == 'on':
                required_fields.append('result')
            if request.POST.get('required_details') == 'on':
                required_fields.append('details')
            
            # Template oluştur
            template = LogVerificationTemplate.objects.create(
                company=company,
                name=name,
                description=description,
                hash_algorithm=hash_algorithm,
                verification_rules=verification_rules,
                required_fields=required_fields,
                auto_generate_report=auto_generate_report,
                report_format=report_format,
                is_active=is_active
            )
            
            messages.success(request, 'Doğrulama şablonu başarıyla oluşturuldu.')
            return redirect('log_verification:templates_list', company.slug)
            
        except Exception as e:
            messages.error(request, f'Oluşturma hatası: {str(e)}')
    
    context = {
        'company': company,
    }
    
    return render(request, 'log_verification/template_add.html', context)


# @login_required  # Geçici olarak kapatıldı
def template_edit(request, company_slug, template_id):
    """Template düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    template = get_object_or_404(LogVerificationTemplate, id=template_id, company=company)
    
    if request.method == 'POST':
        try:
            import json
            
            # Form verilerini al
            template.name = request.POST.get('name')
            template.description = request.POST.get('description', '')
            template.hash_algorithm = request.POST.get('hash_algorithm', 'SHA256')
            template.auto_generate_report = request.POST.get('auto_generate_report') == 'on'
            template.report_format = request.POST.get('report_format', 'PDF')
            template.is_active = request.POST.get('is_active') == 'on'
            
            # Doğrulama kurallarını al
            verification_rules = {
                'hash_verification': request.POST.get('hash_verification') == 'on',
                'signature_verification': request.POST.get('signature_verification') == 'on',
                'integrity_check': request.POST.get('integrity_check') == 'on',
                'timestamp_validation': request.POST.get('timestamp_validation') == 'on'
            }
            template.verification_rules = verification_rules
            
            # Zorunlu alanları al
            required_fields = []
            if request.POST.get('required_timestamp') == 'on':
                required_fields.append('timestamp')
            if request.POST.get('required_user_id') == 'on':
                required_fields.append('user_id')
            if request.POST.get('required_action') == 'on':
                required_fields.append('action')
            if request.POST.get('required_ip_address') == 'on':
                required_fields.append('ip_address')
            if request.POST.get('required_result') == 'on':
                required_fields.append('result')
            if request.POST.get('required_details') == 'on':
                required_fields.append('details')
            template.required_fields = required_fields
            
            template.save()
            
            messages.success(request, 'Doğrulama şablonu başarıyla güncellendi.')
            return redirect('log_verification:templates_list', company.slug)
            
        except Exception as e:
            messages.error(request, f'Güncelleme hatası: {str(e)}')
    
    context = {
        'company': company,
        'template': template,
    }
    
    return render(request, 'log_verification/template_edit.html', context)


# @login_required  # Geçici olarak kapatıldı
def template_delete(request, company_slug, template_id):
    """Template silme"""
    company = get_object_or_404(Company, slug=company_slug)
    template = get_object_or_404(LogVerificationTemplate, id=template_id, company=company)
    
    if request.method == 'POST':
        try:
            template_name = template.name
            template.delete()
            messages.success(request, f'"{template_name}" şablonu başarıyla silindi.')
            return redirect('log_verification:templates_list', company.slug)
        except Exception as e:
            messages.error(request, f'Silme hatası: {str(e)}')
            return redirect('log_verification:templates_list', company.slug)
    
    # GET isteği için onay sayfası göster
    context = {
        'company': company,
        'template': template,
    }
    
    return render(request, 'log_verification/template_delete.html', context)
