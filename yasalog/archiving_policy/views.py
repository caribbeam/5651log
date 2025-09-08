from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from log_kayit.models import Company, CompanyUser
from .models import ArchivingPolicy, ArchivingJob, ArchivingStorage, ArchivingLog


@login_required
def dashboard(request, company_slug):
    """Arşivleme politikası dashboard"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    # İstatistikler
    policies = ArchivingPolicy.objects.filter(company=company)
    active_policies = policies.filter(is_active=True)
    jobs = ArchivingJob.objects.filter(policy__company=company)
    
    context = {
        'company': company,
        'policies': policies,
        'active_policies': active_policies,
        'jobs': jobs,
    }
    
    return render(request, 'archiving_policy/dashboard.html', context)


@login_required
def policies_list(request, company_slug):
    """Policies listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    policies = ArchivingPolicy.objects.filter(company=company)
    
    context = {
        'company': company,
        'policies': policies,
    }
    
    return render(request, 'archiving_policy/policies_list.html', context)


@login_required
def policy_detail(request, company_slug, policy_id):
    """Policy detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    policy = get_object_or_404(ArchivingPolicy, id=policy_id, company=company)
    jobs = ArchivingJob.objects.filter(policy=policy)
    
    context = {
        'company': company,
        'policy': policy,
        'jobs': jobs,
    }
    
    return render(request, 'archiving_policy/policy_detail.html', context)


@login_required
def jobs_list(request, company_slug):
    """Jobs listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    jobs = ArchivingJob.objects.filter(policy__company=company)
    
    context = {
        'company': company,
        'jobs': jobs,
    }
    
    return render(request, 'archiving_policy/jobs_list.html', context)


@login_required
def storage_list(request, company_slug):
    """Storage listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    storages = ArchivingStorage.objects.filter(company=company)
    
    context = {
        'company': company,
        'storages': storages,
    }
    
    return render(request, 'archiving_policy/storage_list.html', context)


@login_required
def logs_list(request, company_slug):
    """Logs listesi"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    logs = ArchivingLog.objects.filter(policy__company=company)
    
    context = {
        'company': company,
        'logs': logs,
    }
    
    return render(request, 'archiving_policy/logs_list.html', context)


# API Views
@login_required
def api_execute_policy(request, company_slug, policy_id):
    """Execute policy API"""
    company = get_object_or_404(Company, slug=company_slug)
    policy = get_object_or_404(ArchivingPolicy, id=policy_id, company=company)
    
    # Yeni job oluştur
    job = ArchivingJob.objects.create(
        policy=policy,
        job_name=f"Manual execution - {policy.name}"
    )
    
    return JsonResponse({'status': 'success', 'message': 'Policy execution started', 'job_id': job.id})


@login_required
def api_job_status(request, company_slug, job_id):
    """Job status API"""
    company = get_object_or_404(Company, slug=company_slug)
    job = get_object_or_404(ArchivingJob, id=job_id, policy__company=company)
    
    return JsonResponse({
        'status': 'success',
        'job_status': job.status,
        'progress': 100 if job.status == 'COMPLETED' else 0
    })


@login_required
def api_storage_capacity(request, company_slug, storage_id):
    """Storage capacity API"""
    company = get_object_or_404(Company, slug=company_slug)
    storage = get_object_or_404(ArchivingStorage, id=storage_id, company=company)
    
    storage.update_capacity()
    
    return JsonResponse({
        'status': 'success',
        'total_capacity': storage.total_capacity_gb,
        'used_capacity': storage.used_capacity_gb,
        'available_capacity': storage.available_capacity_gb,
        'usage_percentage': storage.get_usage_percentage()
    })


# Eksik view'lar
@login_required
def policy_add(request, company_slug):
    """Policy ekleme - şimdilik admin'e yönlendir"""
    return redirect('/admin/archiving_policy/archivingpolicy/add/')


@login_required
def policy_edit(request, company_slug, policy_id):
    """Policy düzenleme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/archiving_policy/archivingpolicy/{policy_id}/change/')


@login_required
def policy_delete(request, company_slug, policy_id):
    """Policy silme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/archiving_policy/archivingpolicy/{policy_id}/delete/')


@login_required
def policy_execute(request, company_slug, policy_id):
    """Policy çalıştır"""
    company = get_object_or_404(Company, slug=company_slug)
    policy = get_object_or_404(ArchivingPolicy, id=policy_id, company=company)
    
    # Yeni job oluştur
    job = ArchivingJob.objects.create(
        policy=policy,
        job_name=f"Manual execution - {policy.name}"
    )
    
    messages.success(request, 'Arşivleme işlemi başlatıldı.')
    return redirect('archiving_policy:policy_detail', company.slug, policy.id)


@login_required
def job_detail(request, company_slug, job_id):
    """Job detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    job = get_object_or_404(ArchivingJob, id=job_id, policy__company=company)
    
    context = {
        'company': company,
        'job': job,
    }
    
    return render(request, 'archiving_policy/job_detail.html', context)


@login_required
def job_cancel(request, company_slug, job_id):
    """Job iptal et"""
    company = get_object_or_404(Company, slug=company_slug)
    job = get_object_or_404(ArchivingJob, id=job_id, policy__company=company)
    
    job.status = 'CANCELLED'
    job.save()
    messages.success(request, 'Arşivleme işi iptal edildi.')
    
    return redirect('archiving_policy:job_detail', company.slug, job.id)


@login_required
def storage_add(request, company_slug):
    """Storage ekleme - şimdilik admin'e yönlendir"""
    return redirect('/admin/archiving_policy/archivingstorage/add/')


@login_required
def storage_detail(request, company_slug, storage_id):
    """Storage detayı"""
    company = get_object_or_404(Company, slug=company_slug)
    storage = get_object_or_404(ArchivingStorage, id=storage_id, company=company)
    
    context = {
        'company': company,
        'storage': storage,
    }
    
    return render(request, 'archiving_policy/storage_detail.html', context)


@login_required
def storage_edit(request, company_slug, storage_id):
    """Storage düzenleme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/archiving_policy/archivingstorage/{storage_id}/change/')


@login_required
def storage_delete(request, company_slug, storage_id):
    """Storage silme - şimdilik admin'e yönlendir"""
    return redirect(f'/admin/archiving_policy/archivingstorage/{storage_id}/delete/')
