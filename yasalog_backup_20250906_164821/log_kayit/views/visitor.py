from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from ..forms import GirisForm
from ..models import LogKayit, Company
from ..services import generate_log_hash
from django.urls import reverse
from django.http import HttpResponseRedirect

def get_mac_from_request(request):
    """
    Gets a unique identifier from the request, falling back to a dummy MAC address.
    In a real-world scenario, this might be based on the user-agent or other headers,
    as getting a real MAC address is not feasible over HTTP.
    """
    # In a real captive portal, the MAC is often passed as a query param
    # e.g., request.GET.get('mac', 'unknown-mac')
    return request.META.get('HTTP_USER_AGENT', '00:00:00:00:00:00')

def giris_view(request, company_id=None, company_slug=None):
    """
    Handles the visitor log entry process.
    - Checks if the device has a recent successful login. If so, creates a new
      log and bypasses the form.
    - If no company is specified, it shows an informational page.
    - If a company is specified, it displays the log entry form for that company.
    - Processes form submission, creates a log entry, and generates a hash.
    """
    # If no slug or id is specified, this is a generic access attempt.
    # Redirect the visitor to an informational page to use the specific link.
    if company_slug is None and company_id is None:
        return render(request, 'log_kayit/giris_landing.html')

    # Find the company by either slug or ID
    if company_slug:
        company_instance = get_object_or_404(Company, slug=company_slug)
    else: # company_id must be present
        company_instance = get_object_or_404(Company, id=company_id)

    # --- Start: Remember Device Feature ---
    # Check for a recent, valid login from this device (identified by MAC/User-Agent)
    # The check is only performed for GET requests to avoid bypassing the form submission logic.
    if request.method == 'GET':
        mac_adresi = get_mac_from_request(request)
        zaman_siniri = timezone.now() - timedelta(hours=24)

        recent_log = LogKayit.objects.filter(
            mac_adresi=mac_adresi,
            company=company_instance,
            giris_zamani__gte=zaman_siniri,
            is_suspicious=False
        ).order_by('-giris_zamani').first()

        if recent_log:
            # Device is recognized. Create a new log for this session to comply with 5651.
            new_log_data = {
                'company': company_instance,
                'ip_adresi': request.META.get('REMOTE_ADDR', '0.0.0.0'),
                'mac_adresi': mac_adresi,
                'kimlik_turu': recent_log.kimlik_turu,
                'tc_no': recent_log.tc_no,
                'pasaport_no': recent_log.pasaport_no,
                'pasaport_ulkesi': recent_log.pasaport_ulkesi,
                'ad_soyad': recent_log.ad_soyad,
                'telefon': recent_log.telefon,
            }
            new_log = LogKayit.objects.create(**new_log_data)

            # Re-generate hash for the new log entry with the new timestamp
            new_log.sha256_hash = generate_log_hash(
                new_log.tc_no, new_log.ad_soyad, new_log.telefon, new_log.ip_adresi, new_log.mac_adresi, new_log.giris_zamani
            )
            new_log.save()
            # Son giriş ve kalan süre hesapla
            last_login = recent_log.giris_zamani
            expires_at = last_login + timedelta(hours=24)
            remaining = expires_at - timezone.now()
            remaining_seconds = int(remaining.total_seconds())
            if remaining_seconds < 0:
                remaining_seconds = 0
            hours = remaining_seconds // 3600
            minutes = (remaining_seconds % 3600) // 60
            remaining_str = f"{hours} saat {minutes} dakika"
            # Ek bilgilendirme
            ip_adresi = request.META.get('REMOTE_ADDR', '0.0.0.0')
            user_agent = request.META.get('HTTP_USER_AGENT', 'Bilinmiyor')
            giris_turu = recent_log.kimlik_turu
            mac_adresi = recent_log.mac_adresi
            return render(request, 'log_kayit/tesekkur.html', {
                'company': company_instance,
                'last_login': last_login,
                'remaining_str': remaining_str,
                'ip_adresi': ip_adresi,
                'user_agent': user_agent,
                'giris_turu': giris_turu,
                'mac_adresi': mac_adresi,
            })
    # --- End: Remember Device Feature ---

    def _prepare_context(form):
        """Prepares the context dictionary for rendering the template."""
        theme_color = company_instance.theme_color if company_instance else "#0d6efd"
        kvkk_text = company_instance.kvkk_text if company_instance else None
        login_info_text = company_instance.login_info_text if company_instance else None
        allow_foreigners = company_instance.allow_foreigners if company_instance else True
        return {
            'form': form, 
            'company': company_instance, 
            'theme_color': theme_color, 
            'kvkk_text': kvkk_text, 
            'login_info_text': login_info_text, 
            'allow_foreigners': allow_foreigners
        }

    if request.method == 'POST':
        form = GirisForm(request.POST, user=request.user, company_instance=company_instance)
        if form.is_valid():
            log = form.save(commit=False)
            log.company = company_instance
            log.ip_adresi = request.META.get('REMOTE_ADDR', '0.0.0.0')
            log.mac_adresi = get_mac_from_request(request)
            
            # Save first to get the timestamp from the database
            log.save()

            # Now, generate the hash with the timestamp and save again
            log.sha256_hash = generate_log_hash(
                log.tc_no, log.ad_soyad, log.telefon, log.ip_adresi, log.mac_adresi, log.giris_zamani
            )
            log.save()
            # Son giriş ve kalan süre hesapla
            last_login = log.giris_zamani
            expires_at = last_login + timedelta(hours=24)
            remaining = expires_at - timezone.now()
            remaining_seconds = int(remaining.total_seconds())
            if remaining_seconds < 0:
                remaining_seconds = 0
            hours = remaining_seconds // 3600
            minutes = (remaining_seconds % 3600) // 60
            remaining_str = f"{hours} saat {minutes} dakika"
            # Ek bilgilendirme
            ip_adresi = request.META.get('REMOTE_ADDR', '0.0.0.0')
            user_agent = request.META.get('HTTP_USER_AGENT', 'Bilinmiyor')
            giris_turu = log.kimlik_turu
            mac_adresi = log.mac_adresi
            return render(request, 'log_kayit/tesekkur.html', {
                'company': log.company,
                'last_login': last_login,
                'remaining_str': remaining_str,
                'ip_adresi': ip_adresi,
                'user_agent': user_agent,
                'giris_turu': giris_turu,
                'mac_adresi': mac_adresi,
            })
        else:
            # Create a log entry for suspicious attempts as well
            if hasattr(form, 'is_suspicious') and form.is_suspicious:
                LogKayit.objects.create(
                    company=company_instance,
                    tc_no=form.data.get('tc_no', ''),
                    pasaport_no=form.data.get('pasaport_no', ''),
                    kimlik_turu=form.data.get('kimlik_turu', 'TC'),
                    ad_soyad=form.data.get('ad_soyad', ''),
                    telefon=form.data.get('telefon', ''),
                    ip_adresi=request.META.get('REMOTE_ADDR', '0.0.0.0'),
                    mac_adresi=get_mac_from_request(request),
                    is_suspicious=True
                )
            context = _prepare_context(form)
            return render(request, 'log_kayit/giris.html', context)
    else:
        form = GirisForm(user=request.user, company_instance=company_instance)
    
    context = _prepare_context(form)
    return render(request, 'log_kayit/giris.html', context)

def cikis_view(request, company_slug=None):
    """
    Cihazı unut (son logları sil) ve giriş formuna yönlendir.
    """
    if not company_slug:
        return HttpResponseRedirect(reverse('giris_landing'))
    company_instance = get_object_or_404(Company, slug=company_slug)
    mac_adresi = get_mac_from_request(request)
    zaman_siniri = timezone.now() - timedelta(hours=24)
    # Son 24 saatlik logları sil
    LogKayit.objects.filter(
        mac_adresi=mac_adresi,
        company=company_instance,
        giris_zamani__gte=zaman_siniri,
        is_suspicious=False
    ).delete()
    # Giriş formuna yönlendir
    return HttpResponseRedirect(reverse('giris_slug', kwargs={'company_slug': company_slug})) 