from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from log_kayit.models import Company, CompanyUser
from .models import LogVerificationSession, LogVerificationResult, LogIntegrityReport, LogVerificationTemplate


@login_required
def dashboard(request, company_slug):
    """Log doğrulama dashboard"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # İstatistikler
    sessions = LogVerificationSession.objects.filter(company=company)
    recent_sessions = sessions.order_by('-created_at')[:5]
    
    context = {
        'company': company,
        'sessions': sessions,
        'recent_sessions': recent_sessions,
    }
    
    return render(request, 'log_verification/dashboard.html', context)


@login_required
def sessions_list(request, company_slug):
    """Verification session listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    sessions = LogVerificationSession.objects.filter(company=company)
    
    context = {
        'company': company,
        'sessions': sessions,
    }
    
    return render(request, 'log_verification/sessions_list.html', context)


@login_required
def session_detail(request, company_slug, session_id):
    """Session detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    results = LogVerificationResult.objects.filter(session=session)
    
    context = {
        'company': company,
        'session': session,
        'results': results,
    }
    
    return render(request, 'log_verification/session_detail.html', context)


@login_required
def results_list(request, company_slug, session_id):
    """Verification results listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    results = LogVerificationResult.objects.filter(session=session)
    
    context = {
        'company': company,
        'session': session,
        'results': results,
    }
    
    return render(request, 'log_verification/results_list.html', context)


@login_required
def reports_list(request, company_slug, session_id):
    """Reports listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    session = get_object_or_404(LogVerificationSession, id=session_id, company=company)
    reports = LogIntegrityReport.objects.filter(session=session)
    
    context = {
        'company': company,
        'session': session,
        'reports': reports,
    }
    
    return render(request, 'log_verification/reports_list.html', context)


@login_required
def templates_list(request, company_slug):
    """Templates listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
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


# Eksik view'lar
@login_required
def session_add(request, company_slug):
    """Session ekleme - şimdilik admin'e yönlendir"""
    return redirect('/admin/log_verification/logverificationsession/add/')


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


@login_required
def result_detail(request, company_slug, result_id):
    """Result detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    result = get_object_or_404(LogVerificationResult, id=result_id, session__company=company)
    
    context = {
        'company': company,
        'result': result,
    }
    
    return render(request, 'log_verification/result_detail.html', context)


@login_required
def report_detail(request, company_slug, report_id):
    """Report detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(LogIntegrityReport, id=report_id, session__company=company)
    
    context = {
        'company': company,
        'report': report,
    }
    
    return render(request, 'log_verification/report_detail.html', context)


@login_required
def report_download(request, company_slug, report_id):
    """Report indir"""
    company = get_object_or_404(Company, slug=company_slug)
    report = get_object_or_404(LogIntegrityReport, id=report_id, session__company=company)
    
    if report.report_file:
        return redirect(report.report_file.url)
    else:
        messages.error(request, 'Rapor dosyası bulunamadı.')
        return redirect('log_verification:report_detail', company.slug, report.id)


@login_required
def template_add(request, company_slug):
    """Template ekleme - şimdilik admin'e yönlendir"""
    return redirect('/admin/log_verification/logverificationtemplate/add/')


@login_required
def template_edit(request, company_slug, template_id):
    """Template düzenleme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/log_verification/logverificationtemplate/{template_id}/change/')


@login_required
def template_delete(request, company_slug, template_id):
    """Template silme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/log_verification/logverificationtemplate/{template_id}/delete/')
