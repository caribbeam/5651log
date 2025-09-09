from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from log_kayit.models import Company, CompanyUser
from .models import ArchivingPolicy, ArchivingJob, ArchivingStorage, ArchivingLog


# @login_required  # Geçici olarak kapatıldı
def dashboard(request, company_slug):
    """Arşivleme politikası dashboard"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü (geçici olarak kapatıldı)
    # if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
    #     return HttpResponseForbidden("Yetkisiz erişim.")
    
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
# @login_required  # Geçici olarak kapatıldı
def policy_add(request, company_slug):
    """Policy ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            policy_type = request.POST.get('policy_type')
            retention_period_years = int(request.POST.get('retention_period_years', 2))
            retention_period_months = int(request.POST.get('retention_period_months', 0))
            retention_period_days = int(request.POST.get('retention_period_days', 0))
            storage_type = request.POST.get('storage_type')
            cleanup_schedule = request.POST.get('cleanup_schedule', 'WEEKLY')
            is_active = 'is_active' in request.POST
            
            # Policy oluştur
            policy = ArchivingPolicy.objects.create(
                company=company,
                name=name,
                description=description,
                policy_type=policy_type,
                retention_period_years=retention_period_years,
                retention_period_months=retention_period_months,
                retention_period_days=retention_period_days,
                storage_type=storage_type,
                cleanup_schedule=cleanup_schedule,
                is_active=is_active
            )
            
            messages.success(request, 'Arşivleme politikası başarıyla oluşturuldu.')
            return redirect('archiving_policy:policy_detail', company.slug, policy.id)
            
        except Exception as e:
            messages.error(request, f'Politika oluşturma hatası: {str(e)}')
    
    context = {
        'company': company,
    }
    
    return render(request, 'archiving_policy/policy_add.html', context)


# @login_required  # Geçici olarak kapatıldı
def policy_edit(request, company_slug, policy_id):
    """Policy düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    policy = get_object_or_404(ArchivingPolicy, id=policy_id, company=company)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            name = request.POST.get('name')
            description = request.POST.get('description', '')
            policy_type = request.POST.get('policy_type')
            retention_period_years = int(request.POST.get('retention_period_years', 2))
            retention_period_months = int(request.POST.get('retention_period_months', 0))
            retention_period_days = int(request.POST.get('retention_period_days', 0))
            storage_type = request.POST.get('storage_type')
            cleanup_schedule = request.POST.get('cleanup_schedule', 'WEEKLY')
            is_active = 'is_active' in request.POST
            
            # Policy güncelle
            policy.name = name
            policy.description = description
            policy.policy_type = policy_type
            policy.retention_period_years = retention_period_years
            policy.retention_period_months = retention_period_months
            policy.retention_period_days = retention_period_days
            policy.storage_type = storage_type
            policy.cleanup_schedule = cleanup_schedule
            policy.is_active = is_active
            policy.save()
            
            messages.success(request, 'Arşivleme politikası başarıyla güncellendi.')
            return redirect('archiving_policy:policy_detail', company.slug, policy.id)
            
        except Exception as e:
            messages.error(request, f'Güncelleme hatası: {str(e)}')
    
    context = {
        'company': company,
        'policy': policy,
    }
    
    return render(request, 'archiving_policy/policy_edit.html', context)


# @login_required  # Geçici olarak kapatıldı
def policy_delete(request, company_slug, policy_id):
    """Policy silme"""
    company = get_object_or_404(Company, slug=company_slug)
    policy = get_object_or_404(ArchivingPolicy, id=policy_id, company=company)
    
    if request.method == 'POST':
        try:
            policy_name = policy.name
            policy.delete()
            messages.success(request, f'"{policy_name}" politikası başarıyla silindi.')
            return redirect('archiving_policy:policies_list', company.slug)
            
        except Exception as e:
            messages.error(request, f'Silme hatası: {str(e)}')
    
    context = {
        'company': company,
        'policy': policy,
    }
    
    return render(request, 'archiving_policy/policy_delete.html', context)


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


# @login_required  # Geçici olarak kapatıldı
def storage_add(request, company_slug):
    """Storage ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            name = request.POST.get('name')
            storage_type = request.POST.get('storage_type')
            storage_path = request.POST.get('storage_path')
            total_capacity_gb = int(request.POST.get('total_capacity_gb', 1000))
            used_capacity_gb = int(request.POST.get('used_capacity_gb', 0))
            is_encrypted = 'is_encrypted' in request.POST
            is_compressed = 'is_compressed' in request.POST
            is_worm = 'is_worm' in request.POST
            worm_append_only = 'worm_append_only' in request.POST
            
            # Available capacity hesapla
            available_capacity_gb = total_capacity_gb - used_capacity_gb
            
            # Storage oluştur
            storage = ArchivingStorage.objects.create(
                company=company,
                name=name,
                storage_type=storage_type,
                storage_path=storage_path,
                total_capacity_gb=total_capacity_gb,
                used_capacity_gb=used_capacity_gb,
                available_capacity_gb=available_capacity_gb,
                is_encrypted=is_encrypted,
                is_compressed=is_compressed,
                is_worm=is_worm,
                worm_append_only=worm_append_only
            )
            
            messages.success(request, 'Depolama alanı başarıyla oluşturuldu.')
            return redirect('archiving_policy:storage_detail', company.slug, storage.id)
            
        except Exception as e:
            messages.error(request, f'Depolama oluşturma hatası: {str(e)}')
    
    context = {
        'company': company,
    }
    
    return render(request, 'archiving_policy/storage_add.html', context)


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


# @login_required  # Geçici olarak kapatıldı
def storage_edit(request, company_slug, storage_id):
    """Storage düzenleme"""
    company = get_object_or_404(Company, slug=company_slug)
    storage = get_object_or_404(ArchivingStorage, id=storage_id, company=company)
    
    if request.method == 'POST':
        try:
            # Form verilerini al
            name = request.POST.get('name')
            storage_type = request.POST.get('storage_type')
            storage_path = request.POST.get('storage_path')
            total_capacity_gb = int(request.POST.get('total_capacity_gb', 1000))
            used_capacity_gb = int(request.POST.get('used_capacity_gb', 0))
            is_encrypted = 'is_encrypted' in request.POST
            is_compressed = 'is_compressed' in request.POST
            is_worm = 'is_worm' in request.POST
            worm_append_only = 'worm_append_only' in request.POST
            
            # Available capacity hesapla
            available_capacity_gb = total_capacity_gb - used_capacity_gb
            
            # Storage güncelle
            storage.name = name
            storage.storage_type = storage_type
            storage.storage_path = storage_path
            storage.total_capacity_gb = total_capacity_gb
            storage.used_capacity_gb = used_capacity_gb
            storage.available_capacity_gb = available_capacity_gb
            storage.is_encrypted = is_encrypted
            storage.is_compressed = is_compressed
            storage.is_worm = is_worm
            storage.worm_append_only = worm_append_only
            storage.save()
            
            messages.success(request, 'Depolama alanı başarıyla güncellendi.')
            return redirect('archiving_policy:storage_detail', company.slug, storage.id)
            
        except Exception as e:
            messages.error(request, f'Güncelleme hatası: {str(e)}')
    
    context = {
        'company': company,
        'storage': storage,
    }
    
    return render(request, 'archiving_policy/storage_edit.html', context)


# @login_required  # Geçici olarak kapatıldı
def storage_delete(request, company_slug, storage_id):
    """Storage silme"""
    company = get_object_or_404(Company, slug=company_slug)
    storage = get_object_or_404(ArchivingStorage, id=storage_id, company=company)
    
    if request.method == 'POST':
        try:
            storage_name = storage.name
            storage.delete()
            messages.success(request, f'"{storage_name}" depolama alanı başarıyla silindi.')
            return redirect('archiving_policy:storage_list', company.slug)
            
        except Exception as e:
            messages.error(request, f'Silme hatası: {str(e)}')
    
    context = {
        'company': company,
        'storage': storage,
    }
    
    return render(request, 'archiving_policy/storage_delete.html', context)
