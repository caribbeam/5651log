"""
Profile Management Views
5651log platformunda profil yönetimi için frontend view'ları
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import UserProfile, UserProfileAssignment
from log_kayit.models import Company

@login_required
def profile_dashboard(request, company_slug):
    """Profil yönetimi ana dashboard'u"""
    
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Şirket bulunamadı!")
        return redirect('log_kayit:dashboard')
    
    # Profil istatistikleri
    total_profiles = UserProfile.objects.filter(company=company).count()
    active_profiles = UserProfile.objects.filter(company=company, is_active=True).count()
    total_assignments = UserProfileAssignment.objects.filter(company=company).count()
    active_assignments = UserProfileAssignment.objects.filter(company=company, is_active=True).count()
    
    # Son eklenen profiller
    recent_profiles = UserProfile.objects.filter(company=company).order_by('-created_at')[:5]
    
    # Profil tipi dağılımı
    profile_types = UserProfile.objects.filter(company=company).values('profile_type').distinct()
    
    context = {
        'company': company,
        'total_profiles': total_profiles,
        'active_profiles': active_profiles,
        'total_assignments': total_assignments,
        'active_assignments': active_assignments,
        'recent_profiles': recent_profiles,
        'profile_types': profile_types,
    }
    
    return render(request, 'profile_management/dashboard.html', context)

@login_required
def profile_list(request, company_slug):
    """Profil listesi sayfası"""
    
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Şirket bulunamadı!")
        return redirect('log_kayit:dashboard')
    
    # Filtreleme
    search_query = request.GET.get('search', '')
    profile_type = request.GET.get('type', '')
    status = request.GET.get('status', '')
    
    profiles = UserProfile.objects.filter(company=company)
    
    if search_query:
        profiles = profiles.filter(
            Q(name__icontains=search_query) | 
            Q(profile_code__icontains=search_query)
        )
    
    if profile_type:
        profiles = profiles.filter(profile_type=profile_type)
    
    if status == 'active':
        profiles = profiles.filter(is_active=True)
    elif status == 'inactive':
        profiles = profiles.filter(is_active=False)
    
    profiles = profiles.order_by('profile_code')
    
    context = {
        'company': company,
        'profiles': profiles,
        'search_query': search_query,
        'profile_type': profile_type,
        'status': status,
    }
    
    return render(request, 'profile_management/profile_list.html', context)

@login_required
def profile_detail(request, company_slug, profile_id):
    """Profil detay sayfası"""
    
    try:
        company = Company.objects.get(slug=company_slug)
        profile = UserProfile.objects.get(id=profile_id, company=company)
    except (Company.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, "Profil bulunamadı!")
        return redirect('profile_management:profile_list', company_slug=company_slug)
    
    # Bu profile atanan kullanıcılar
    assignments = UserProfileAssignment.objects.filter(profile=profile, company=company)
    
    context = {
        'company': company,
        'profile': profile,
        'assignments': assignments,
    }
    
    return render(request, 'profile_management/profile_detail.html', context)

@login_required
def profile_create(request, company_slug):
    """Yeni profil oluşturma"""
    
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        messages.error(request, "Şirket bulunamadı!")
        return redirect('log_kayit:dashboard')
    
    if request.method == 'POST':
        # Form işleme
        name = request.POST.get('name')
        profile_code = request.POST.get('profile_code')
        profile_type = request.POST.get('profile_type')
        upload_speed = request.POST.get('upload_speed')
        download_speed = request.POST.get('download_speed')
        duration_days = request.POST.get('duration_days', 0)
        shared_users = request.POST.get('shared_users', 1)
        
        try:
            profile = UserProfile.objects.create(
                name=name,
                profile_code=profile_code,
                profile_type=profile_type,
                upload_speed=upload_speed,
                download_speed=download_speed,
                duration_days=duration_days,
                shared_users=shared_users,
                company=company
            )
            messages.success(request, f"'{profile.name}' profili başarıyla oluşturuldu!")
            return redirect('profile_management:profile_detail', company_slug=company_slug, profile_id=profile.id)
        except Exception as e:
            messages.error(request, f"Profil oluşturulurken hata: {str(e)}")
    
    context = {
        'company': company,
        'profile_types': UserProfile.PROFILE_TYPES,
    }
    
    return render(request, 'profile_management/profile_form.html', context)

@login_required
def profile_edit(request, company_slug, profile_id):
    """Profil düzenleme"""
    
    try:
        company = Company.objects.get(slug=company_slug)
        profile = UserProfile.objects.get(id=profile_id, company=company)
    except (Company.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, "Profil bulunamadı!")
        return redirect('profile_management:profile_list', company_slug=company_slug)
    
    if request.method == 'POST':
        # Form güncelleme
        profile.name = request.POST.get('name')
        profile.profile_type = request.POST.get('profile_type')
        profile.upload_speed = request.POST.get('upload_speed')
        profile.download_speed = request.POST.get('download_speed')
        profile.duration_days = request.POST.get('duration_days', 0)
        profile.shared_users = request.POST.get('shared_users', 1)
        profile.is_active = request.POST.get('is_active') == 'on'
        
        try:
            profile.save()
            messages.success(request, f"'{profile.name}' profili başarıyla güncellendi!")
            return redirect('profile_management:profile_detail', company_slug=company_slug, profile_id=profile.id)
        except Exception as e:
            messages.error(request, f"Profil güncellenirken hata: {str(e)}")
    
    context = {
        'company': company,
        'profile': profile,
        'profile_types': UserProfile.PROFILE_TYPES,
    }
    
    return render(request, 'profile_management/profile_form.html', context)

@login_required
def get_profile_data(request, company_slug):
    """AJAX ile profil verisi getir"""
    
    try:
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Şirket bulunamadı'}, status=404)
    
    profiles = UserProfile.objects.filter(company=company, is_active=True)
    
    data = []
    for profile in profiles:
        data.append({
            'id': profile.id,
            'name': profile.name,
            'profile_code': profile.profile_code,
            'profile_type': profile.get_profile_type_display(),
            'speed': profile.get_speed_display(),
            'duration': profile.get_duration_display(),
            'shared_users': profile.shared_users,
        })
    
    return JsonResponse({'profiles': data})
