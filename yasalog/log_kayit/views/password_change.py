from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from ..models import Company, CompanyUser


@login_required
def password_change_view(request, company_slug):
    """Frontend şifre değiştirme sayfası"""
    company = get_object_or_404(Company, slug=company_slug)
    
    # Yetki kontrolü
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden("Yetkisiz erişim.")
    
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Mevcut şifre kontrolü
        if not request.user.check_password(old_password):
            messages.error(request, 'Mevcut şifre yanlış.')
            return render(request, 'log_kayit/password_change.html', {'company': company})
        
        # Yeni şifre eşleşme kontrolü
        if new_password1 != new_password2:
            messages.error(request, 'Yeni şifreler eşleşmiyor.')
            return render(request, 'log_kayit/password_change.html', {'company': company})
        
        # Şifre uzunluk kontrolü
        if len(new_password1) < 8:
            messages.error(request, 'Yeni şifre en az 8 karakter uzunluğunda olmalıdır.')
            return render(request, 'log_kayit/password_change.html', {'company': company})
        
        try:
            # Şifreyi değiştir
            request.user.set_password(new_password1)
            request.user.save()
            
            # Session'ı güncelle (kullanıcıyı logout etmemek için)
            update_session_auth_hash(request, request.user)
            
            messages.success(request, 'Şifreniz başarıyla değiştirildi.')
            return redirect('log_kayit:company_dashboard_slug', company.slug)
            
        except Exception as e:
            messages.error(request, f'Şifre değiştirme hatası: {str(e)}')
    
    context = {
        'company': company,
    }
    
    return render(request, 'log_kayit/password_change.html', context)
