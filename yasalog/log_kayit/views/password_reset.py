from django.shortcuts import render, redirect
from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string


def password_reset_view(request):
    """Frontend şifre sıfırlama sayfası"""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if email:
            try:
                user = User.objects.get(email=email)
                
                # Token oluştur
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                
                # E-posta içeriği
                reset_url = request.build_absolute_uri(
                    reverse('log_kayit:password_reset_confirm', kwargs={
                        'uidb64': uid,
                        'token': token
                    })
                )
                
                subject = 'Şifre Sıfırlama Talebi'
                message = f"""
                Merhaba {user.first_name or user.username},
                
                Şifre sıfırlama talebiniz alınmıştır. Aşağıdaki bağlantıya tıklayarak yeni şifrenizi belirleyebilirsiniz:
                
                {reset_url}
                
                Bu bağlantı 24 saat geçerlidir.
                
                Eğer bu talebi siz yapmadıysanız, bu e-postayı görmezden gelebilirsiniz.
                
                İyi günler,
                5651 Log Sistemi
                """
                
                # E-posta gönder
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                messages.success(request, 'Şifre sıfırlama bağlantısı e-posta adresinize gönderildi.')
                return redirect('log_kayit:password_reset_done')
                
            except User.DoesNotExist:
                messages.error(request, 'Bu e-posta adresi ile kayıtlı kullanıcı bulunamadı.')
            except Exception as e:
                messages.error(request, f'E-posta gönderme hatası: {str(e)}')
        else:
            messages.error(request, 'Lütfen e-posta adresinizi girin.')
    
    context = {
        'company': None,  # Şifre sıfırlama için company gerekli değil
    }
    return render(request, 'log_kayit/password_reset.html', context)


def password_reset_done_view(request):
    """Şifre sıfırlama e-postası gönderildi sayfası"""
    context = {
        'company': None,
    }
    return render(request, 'log_kayit/password_reset_done.html', context)


def password_reset_confirm_view(request, uidb64, token):
    """Şifre sıfırlama onay sayfası"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            
            if new_password1 and new_password2:
                if new_password1 == new_password2:
                    if len(new_password1) >= 8:
                        user.set_password(new_password1)
                        user.save()
                        messages.success(request, 'Şifreniz başarıyla sıfırlandı.')
                        return redirect('log_kayit:password_reset_complete')
                    else:
                        messages.error(request, 'Şifre en az 8 karakter uzunluğunda olmalıdır.')
                else:
                    messages.error(request, 'Şifreler eşleşmiyor.')
            else:
                messages.error(request, 'Lütfen tüm alanları doldurun.')
        
        context = {
            'company': None,
            'validlink': True,
        }
        return render(request, 'log_kayit/password_reset_confirm.html', context)
    else:
        context = {
            'company': None,
            'validlink': False,
        }
        return render(request, 'log_kayit/password_reset_confirm.html', context)


def password_reset_complete_view(request):
    """Şifre sıfırlama tamamlandı sayfası"""
    context = {
        'company': None,
    }
    return render(request, 'log_kayit/password_reset_complete.html', context)
