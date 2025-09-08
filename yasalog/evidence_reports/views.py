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
    """Report ekleme - şimdilik admin'e yönlendir"""
    return redirect('/admin/evidence_reports/evidencereport/add/')


@login_required
def report_edit(request, company_slug, report_id):
    """Report düzenleme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/evidence_reports/evidencereport/{report_id}/change/')


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
    """Template ekleme - şimdilik admin'e yönlendir"""
    return redirect('/admin/evidence_reports/evidencereporttemplate/add/')


@login_required
def template_edit(request, company_slug, template_id):
    """Template düzenleme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/evidence_reports/evidencereporttemplate/{template_id}/change/')


@login_required
def template_delete(request, company_slug, template_id):
    """Template silme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/evidence_reports/evidencereporttemplate/{template_id}/delete/')
