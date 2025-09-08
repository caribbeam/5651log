from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django import forms
from django.urls import reverse
from django.db.models import Count
from django.utils.translation import gettext as _

from ..models import Company, CompanyUser, LogKayit
from ..forms import CompanySettingsForm

@login_required
def company_user_panel(request):
    """
    Redirects the logged-in user to the dashboard of their first associated company.
    Superusers are redirected to the first company's dashboard by default.
    """
    user = request.user

    # Önce kullanıcının kendi firmasını kontrol et
    company_user = CompanyUser.objects.filter(user=user).select_related('company').first()
    
    if company_user and company_user.company.slug:
        return redirect('log_kayit:company_dashboard_slug', company_slug=company_user.company.slug)
    
    # Eğer kendi firması yoksa ve superuser ise ilk firmaya yönlendir
    if user.is_superuser:
        first_company = Company.objects.first()
        if first_company and first_company.slug:
            return redirect('log_kayit:company_dashboard_slug', company_slug=first_company.slug)
        return redirect('/admin/')
    
    messages.error(request, _("You are not associated with any company. Please contact an administrator."))
    return redirect('yonetici_login')

@login_required
def user_management_view(request):
    """
    Handles user management for a specific company.
    - Superusers can switch between companies.
    - Company admins can manage users of their own company.
    - Handles POST requests to activate/deactivate users and change their roles.
    """
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

    if request.method == 'POST':
        user_to_change_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user_to_change_cu = get_object_or_404(CompanyUser, id=user_to_change_id, company=user_company)
        user_to_change = user_to_change_cu.user

        if action == 'toggle_active':
            if user_to_change == request.user:
                messages.error(request, _("You cannot deactivate your own account."))
            else:
                user_to_change.is_active = not user_to_change.is_active
                user_to_change.save()
                messages.success(request, _("User '{username}' status has been updated.").format(username=user_to_change.username))
        
        elif action == 'change_role':
            new_role = request.POST.get('role')
            if new_role in [role[0] for role in CompanyUser.ROLE_CHOICES]:
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

        redirect_url = reverse('user_management_view')
        return redirect(f'{redirect_url}?company={user_company.id}')

    users = CompanyUser.objects.filter(company=user_company).select_related('user')
    log_counts = LogKayit.objects.filter(company=user_company).values('ad_soyad').annotate(count=Count('id')).order_by()
    log_counts_dict = {item['ad_soyad']: item['count'] for item in log_counts}

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
        'all_companies': all_companies if request.user.is_superuser else None,
        'user_stats': user_stats,
    })

@login_required
def company_settings_panel(request):
    """
    Handles the company settings form.
    - Superusers can see and edit settings for any company.
    - Company admins can edit their own company's settings.
    """
    if request.user.is_superuser:
        all_companies = Company.objects.all()
        company_id = request.GET.get('company')
        company = Company.objects.filter(id=company_id).first() if company_id else all_companies.first()
    else:
        all_companies = None
        company_user = CompanyUser.objects.filter(user=request.user, role='admin').first()
        if not company_user:
            return HttpResponseForbidden(_("You are not authorized to view this page."))
        company = company_user.company

    if not company:
        messages.error(request, _("No company found to display settings for."))
        return render(request, 'log_kayit/company_settings_panel.html', {'is_superuser': request.user.is_superuser})

    if request.method == 'POST':
        form = CompanySettingsForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            form.save()
            messages.success(request, _('Settings saved successfully.'))
            # Redirect to the same company's settings page
            return redirect(f"{reverse('company_settings_panel')}?company={company.id}")
        else:
            messages.error(request, _('Could not save settings. Please check the form.'))
    else:
        form = CompanySettingsForm(instance=company)
        
    return render(request, 'log_kayit/company_settings_panel.html', {
        'form': form, 
        'company': company, 
        'all_companies': all_companies
    }) 