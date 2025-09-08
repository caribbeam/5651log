"""
Gelişmiş kullanıcı yönetimi view'ları
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db import transaction
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from ..models import Company, CompanyUser, UserPermission, UserActivityLog
from ..forms import CompanyUserCreationForm, CompanyUserEditForm, UserPermissionForm, BulkUserCreationForm
from ..decorators import require_company_admin, log_user_activity, check_user_permissions


@login_required
@require_company_admin
@log_user_activity('manage_user')
def user_management_dashboard(request, company_slug):
    """Kullanıcı yönetimi ana sayfası"""
    # Company slug ile şirketi bul
    company = get_object_or_404(Company, slug=company_slug)
    
    # Kullanıcıları getir
    users = CompanyUser.objects.filter(company=company).select_related('user').prefetch_related('permissions')
    
    # Arama
    search = request.GET.get('search')
    if search:
        users = users.filter(
            user__username__icontains=search,
            user__first_name__icontains=search,
            user__last_name__icontains=search,
            user__email__icontains=search
        )
    
    # Rol filtresi
    role_filter = request.GET.get('role_filter')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Sayfalama
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    context = {
        'company': company,
        'users': users_page,
        'search': search,
        'total_users': users.count(),
        'active_users': users.filter(user__is_active=True).count(),
        'admin_count': users.filter(role='admin').count(),
        'staff_count': users.filter(role='staff').count(),
        'viewer_count': users.filter(role='viewer').count(),
    }
    
    return render(request, 'log_kayit/user_management_dashboard.html', context)


@login_required
@require_company_admin
@log_user_activity('manage_user')
def add_user(request, company_slug):
    """Yeni kullanıcı ekleme"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        form = CompanyUserCreationForm(request.POST, company=company)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    company_user = CompanyUser.objects.get(user=user, company=company)
                    
                    # Varsayılan yetkiler oluştur
                    UserPermission.objects.create(
                        company_user=company_user,
                        can_view_dashboard=True,
                        can_view_reports=True,
                        can_export_data=company_user.role in ['admin', 'staff'],
                        can_manage_users=company_user.role == 'admin',
                        can_edit_company_settings=company_user.role == 'admin'
                    )
                    
                    messages.success(request, _("Kullanıcı başarıyla eklendi."))
                    return redirect('user_management_dashboard')
            except Exception as e:
                messages.error(request, f"Kullanıcı eklenirken hata oluştu: {str(e)}")
    else:
        form = CompanyUserCreationForm(company=company)
    
    context = {
        'form': form,
        'company': company,
    }
    return render(request, 'log_kayit/add_user.html', context)


@login_required
@require_company_admin
@log_user_activity('manage_user')
def edit_user(request, user_id, company_slug):
    """Kullanıcı düzenleme"""
    company_user = get_object_or_404(CompanyUser, id=user_id)
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        current_company_user = CompanyUser.objects.get(user=request.user)
        if company_user.company != current_company_user.company:
            messages.error(request, _("Bu kullanıcıyı düzenleme yetkiniz yok."))
            return redirect('user_management_dashboard')
    
    if request.method == 'POST':
        form = CompanyUserEditForm(request.POST, instance=company_user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Kullanıcı başarıyla güncellendi."))
            return redirect('user_management_dashboard')
    else:
        form = CompanyUserEditForm(instance=company_user)
    
    context = {
        'form': form,
        'company_user': company_user,
        'company': company_user.company,
    }
    return render(request, 'log_kayit/edit_user.html', context)


@login_required
@require_company_admin
@log_user_activity('manage_user')
def user_permissions(request, user_id, company_slug):
    """Kullanıcı yetkilerini düzenleme"""
    company_user = get_object_or_404(CompanyUser, id=user_id)
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        current_company_user = CompanyUser.objects.get(user=request.user)
        if company_user.company != current_company_user.company:
            messages.error(request, _("Bu kullanıcının yetkilerini düzenleme yetkiniz yok."))
            return redirect('user_management_dashboard')
    
    permission, created = UserPermission.objects.get_or_create(company_user=company_user)
    
    if request.method == 'POST':
        form = UserPermissionForm(request.POST, instance=permission)
        if form.is_valid():
            form.save()
            messages.success(request, _("Kullanıcı yetkileri başarıyla güncellendi."))
            return redirect('user_management_dashboard')
    else:
        form = UserPermissionForm(instance=permission)
    
    context = {
        'form': form,
        'company_user': company_user,
        'company': company_user.company,
        'permission': permission,
    }
    return render(request, 'log_kayit/user_permissions.html', context)


@login_required
@require_company_admin
@log_user_activity('manage_user')
def bulk_user_creation(request, company_slug):
    """Toplu kullanıcı oluşturma"""
    company = get_object_or_404(Company, slug=company_slug)
    
    if request.method == 'POST':
        form = BulkUserCreationForm(request.POST)
        if form.is_valid():
            users_data = form.cleaned_data['users_data']
            created_count = 0
            error_count = 0
            
            try:
                with transaction.atomic():
                    for user_data in users_data:
                        try:
                            # Kullanıcı oluştur
                            from django.contrib.auth.models import User
                            user = User.objects.create_user(
                                username=user_data['username'],
                                email=user_data['email'],
                                first_name=user_data['first_name'],
                                last_name=user_data['last_name'],
                                password='temp123'  # Geçici şifre
                            )
                            
                            # CompanyUser oluştur
                            company_user = CompanyUser.objects.create(
                                user=user,
                                company=company,
                                role=user_data['role']
                            )
                            
                            # Varsayılan yetkiler
                            UserPermission.objects.create(
                                company_user=company_user,
                                can_view_dashboard=True,
                                can_view_reports=True,
                                can_export_data=user_data['role'] in ['admin', 'staff'],
                                can_manage_users=user_data['role'] == 'admin',
                                can_edit_company_settings=user_data['role'] == 'admin'
                            )
                            
                            created_count += 1
                            
                        except Exception as e:
                            error_count += 1
                            continue
                    
                    messages.success(request, f"{created_count} kullanıcı oluşturuldu. {error_count} hata oluştu.")
                    return redirect('user_management_dashboard')
                    
            except Exception as e:
                messages.error(request, f"Toplu kullanıcı oluşturma hatası: {str(e)}")
    else:
        form = BulkUserCreationForm()
    
    context = {
        'form': form,
        'company': company,
    }
    return render(request, 'log_kayit/bulk_user_creation.html', context)


@login_required
@require_company_admin
@log_user_activity('manage_user')
def user_activity_logs(request, user_id, company_slug):
    """Kullanıcı aktivite logları"""
    company_user = get_object_or_404(CompanyUser, id=user_id)
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        current_company_user = CompanyUser.objects.get(user=request.user)
        if company_user.company != current_company_user.company:
            messages.error(request, _("Bu kullanıcının loglarını görme yetkiniz yok."))
            return redirect('user_management_dashboard')
    
    logs = UserActivityLog.objects.filter(company_user=company_user).order_by('-timestamp')
    
    # Sayfalama
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    logs_page = paginator.get_page(page_number)
    
    context = {
        'company_user': company_user,
        'company': company_user.company,
        'logs': logs_page,
    }
    return render(request, 'log_kayit/user_activity_logs.html', context)


@login_required
@require_company_admin
@require_http_methods(["POST"])
def toggle_user_status(request, user_id, company_slug):
    """Kullanıcı aktif/pasif durumunu değiştir"""
    company_user = get_object_or_404(CompanyUser, id=user_id)
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        current_company_user = CompanyUser.objects.get(user=request.user)
        if company_user.company != current_company_user.company:
            return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    # Kendi hesabını deaktive etmesini önle
    if company_user.user == request.user:
        return JsonResponse({'error': 'Kendi hesabınızı deaktive edemezsiniz'}, status=400)
    
    company_user.user.is_active = not company_user.user.is_active
    company_user.user.save()
    
    status = 'aktif' if company_user.user.is_active else 'pasif'
    return JsonResponse({
        'success': True,
        'message': f'Kullanıcı {status} duruma getirildi',
        'is_active': company_user.user.is_active
    })


@login_required
@require_company_admin
@require_http_methods(["POST"])
def delete_user(request, user_id, company_slug):
    """Kullanıcı silme"""
    company_user = get_object_or_404(CompanyUser, id=user_id)
    
    # Yetki kontrolü
    if not request.user.is_superuser:
        current_company_user = CompanyUser.objects.get(user=request.user)
        if company_user.company != current_company_user.company:
            return JsonResponse({'error': 'Yetkisiz erişim'}, status=403)
    
    # Kendi hesabını silmesini önle
    if company_user.user == request.user:
        return JsonResponse({'error': 'Kendi hesabınızı silemezsiniz'}, status=400)
    
    # Son admin kontrolü
    if company_user.role == 'admin':
        admin_count = CompanyUser.objects.filter(company=company_user.company, role='admin').count()
        if admin_count <= 1:
            return JsonResponse({'error': 'Son yöneticiyi silemezsiniz'}, status=400)
    
    username = company_user.user.username
    company_user.user.delete()
    
    return JsonResponse({
        'success': True,
        'message': f'{username} kullanıcısı silindi'
    })
