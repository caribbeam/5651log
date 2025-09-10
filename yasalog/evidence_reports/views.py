from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from log_kayit.models import Company, CompanyUser
from .models import EvidenceReport, EvidenceReportTemplate, EvidenceReportAccess


@login_required
def dashboard(request, company_slug):
    """İbraz raporları dashboard"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # İstatistikler
    reports = EvidenceReport.objects.filter(company=company)
    recent_reports = reports.order_by('-created_at')[:5]
    
    context = {
        'company': company,
        'reports': reports,
        'recent_reports': recent_reports,
    }
    
    return render(request, 'evidence_reports/dashboard.html', context)


@login_required
def reports_list(request, company_slug):
    """Reports listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    reports = EvidenceReport.objects.filter(company=company)
    
    context = {
        'company': company,
        'reports': reports,
    }
    
    return render(request, 'evidence_reports/reports_list.html', context)


@login_required
def report_detail(request, company_slug, report_id):
    """Report detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    report = get_object_or_404(EvidenceReport, id=report_id, company=company)
    
    context = {
        'company': company,
        'report': report,
    }
    
    return render(request, 'evidence_reports/report_detail.html', context)


@login_required
def templates_list(request, company_slug):
    """Templates listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    templates = EvidenceReportTemplate.objects.filter(company=company)
    
    context = {
        'company': company,
        'templates': templates,
    }
    
    return render(request, 'evidence_reports/templates_list.html', context)


@login_required
def access_logs_list(request, company_slug, report_id):
    """Access logs listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    report = get_object_or_404(EvidenceReport, id=report_id, company=company)
    access_logs = EvidenceReportAccess.objects.filter(report=report)
    
    context = {
        'company': company,
        'report': report,
        'access_logs': access_logs,
    }
    
    return render(request, 'evidence_reports/access_logs_list.html', context)


# API Views
@login_required
def api_generate_report(request, company_slug, report_id):
    """Generate report API"""
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(EvidenceReport, id=report_id, company=company)
    
    report.generate_report(request.user)
    
    return JsonResponse({'status': 'success', 'message': 'Report generation started'})


@login_required
def api_report_status(request, company_slug, report_id):
    """Report status API"""
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(EvidenceReport, id=report_id, company=company)
    
    return JsonResponse({
        'status': 'success',
        'report_status': report.status,
        'progress': 100 if report.status == 'GENERATED' else 0
    })


# Eksik view'lar
@login_required
def report_add(request, company_slug):
    """Report ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            report_title = request.POST.get('report_title')
            report_type = request.POST.get('report_type')
            priority = request.POST.get('priority')
            report_description = request.POST.get('description', '')
            requester_name = request.POST.get('requested_by', '')
            requester_authority = request.POST.get('requester_authority', '')
            deadline = request.POST.get('due_date')
            requested_data_period = request.POST.get('requested_data_period', 'Son 30 gün')
            
            # Talep numarası oluştur
            from django.utils import timezone
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            request_number = f"ER-{timestamp}-{company.id}"
            
            # Report oluştur
            report = EvidenceReport.objects.create(
                company=company,
                report_title=report_title,
                report_type=report_type,
                priority=priority,
                report_description=report_description,
                requester_name=requester_name,
                requester_authority=requester_authority,
                request_number=request_number,
                request_date=timezone.now(),
                start_date=timezone.now(),
                end_date=timezone.now(),
                requested_data_period=requested_data_period,
                deadline=deadline if deadline else None,
                status='DRAFT'
            )
            
            messages.success(request, 'İbraz raporu başarıyla oluşturuldu.')
            return redirect('evidence_reports:report_detail', company.slug, report.id)
            
        except Exception as e:
            messages.error(request, f'Rapor oluşturma hatası: {str(e)}')
    
    context = {
        'company': company,
    }
    
    return render(request, 'evidence_reports/report_add.html', context)


@login_required
def report_edit(request, company_slug, report_id):
    """Report düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(EvidenceReport, id=report_id, company=company)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            report_title = request.POST.get('report_title')
            report_type = request.POST.get('report_type')
            priority = request.POST.get('priority')
            report_description = request.POST.get('description', '')
            requester_name = request.POST.get('requested_by', '')
            requester_authority = request.POST.get('requester_authority', '')
            deadline = request.POST.get('due_date')
            requested_data_period = request.POST.get('requested_data_period', 'Son 30 gün')
            
            # Report güncelle
            report.report_title = report_title
            report.report_type = report_type
            report.priority = priority
            report.report_description = report_description
            report.requester_name = requester_name
            report.requester_authority = requester_authority
            report.requested_data_period = requested_data_period
            report.deadline = deadline if deadline else None
            report.save()
            
            messages.success(request, 'Rapor başarıyla güncellendi.')
            return redirect('evidence_reports:report_detail', company.slug, report.id)
            
        except Exception as e:
            messages.error(request, f'Güncelleme hatası: {str(e)}')
    
    context = {
        'company': company,
        'report': report,
    }
    
    return render(request, 'evidence_reports/report_edit.html', context)


@login_required
def report_approve(request, company_slug, report_id):
    """Report onayla"""
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(EvidenceReport, id=report_id, company=company)
    
    report.approve(request.user)
    messages.success(request, 'Rapor onaylandı.')
    
    return redirect('evidence_reports:report_detail', company.slug, report.id)


@login_required
def report_generate(request, company_slug, report_id):
    """Report oluştur"""
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(EvidenceReport, id=report_id, company=company)
    
    report.generate_report(request.user)
    messages.success(request, 'Rapor oluşturma işlemi başlatıldı.')
    
    return redirect('evidence_reports:report_detail', company.slug, report.id)


@login_required
def report_download(request, company_slug, report_id):
    """Report indir"""
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(EvidenceReport, id=report_id, company=company)
    
    if report.generated_file:
        return redirect(report.generated_file.url)
    else:
        messages.error(request, 'Rapor dosyası bulunamadı.')
        return redirect('evidence_reports:report_detail', company.slug, report.id)


@login_required
def report_deliver(request, company_slug, report_id):
    """Report teslim et"""
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(EvidenceReport, id=report_id, company=company)
    
    report.deliver_report()
    messages.success(request, 'Rapor teslim edildi.')
    
    return redirect('evidence_reports:report_detail', company.slug, report.id)


@login_required
def template_add(request, company_slug):
    """Template ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            name = request.POST.get('template_name')
            report_type = request.POST.get('report_type')
            description = request.POST.get('description', '')
            template_content = request.POST.get('template_content', '')
            is_active = 'is_active' in request.POST
            
            # Template oluştur
            template = EvidenceReportTemplate.objects.create(
                company=company,
                name=name,
                report_type=report_type,
                description=description,
                template_content=template_content,
                is_active=is_active
            )
            
            messages.success(request, 'Şablon başarıyla oluşturuldu.')
            return redirect('evidence_reports:templates_list', company.slug)
            
        except Exception as e:
            messages.error(request, f'Şablon oluşturma hatası: {str(e)}')
    
    context = {
        'company': company,
    }
    
    return render(request, 'evidence_reports/template_add.html', context)


@login_required
def template_edit(request, company_slug, template_id):
    """Template düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    template = get_object_or_404(EvidenceReportTemplate, id=template_id, company=company)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            name = request.POST.get('template_name')
            report_type = request.POST.get('report_type')
            description = request.POST.get('description', '')
            template_content = request.POST.get('template_content', '')
            is_active = 'is_active' in request.POST
            
            # Template güncelle
            template.name = name
            template.report_type = report_type
            template.description = description
            template.template_content = template_content
            template.is_active = is_active
            template.save()
            
            messages.success(request, 'Şablon başarıyla güncellendi.')
            return redirect('evidence_reports:templates_list', company.slug)
            
        except Exception as e:
            messages.error(request, f'Güncelleme hatası: {str(e)}')
    
    context = {
        'company': company,
        'template': template,
    }
    
    return render(request, 'evidence_reports/template_edit.html', context)


@login_required
def template_delete(request, company_slug, template_id):
    """Template silme"""
    company = get_object_or_404(Company, slug=company_slug)
    template = get_object_or_404(EvidenceReportTemplate, id=template_id, company=company)
    
    if request.method == 'POST':
        try:
            template_name = template.name
            template.delete()
            messages.success(request, f'"{template_name}" şablonu başarıyla silindi.')
            return redirect('evidence_reports:templates_list', company.slug)
            
        except Exception as e:
            messages.error(request, f'Silme hatası: {str(e)}')
    
    context = {
        'company': company,
        'template': template,
    }
    
    return render(request, 'evidence_reports/template_delete.html', context)
