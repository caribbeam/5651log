from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse
from django.utils import timezone
from django.utils.translation import gettext as _

from ..models import Company, CompanyUser
from ..exports import export_as_excel, export_as_pdf, export_as_zip
from .dashboard import get_filtered_logs

@login_required
def dashboard_export_excel(request, company_id=None, company_slug=None):
    if company_slug:
        company = get_object_or_404(Company, slug=company_slug)
    elif company_id:
        company = get_object_or_404(Company, id=company_id)
    else:
        return HttpResponseForbidden(_("Company not found."))
    
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden()
        
    logs = get_filtered_logs(request, company)
    output, error = export_as_excel(logs)
    if error:
        return HttpResponse(error, status=400)
        
    response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=loglar_{company.name}_{timezone.now().date()}.xlsx'
    return response

@login_required
def dashboard_export_pdf(request, company_id=None, company_slug=None):
    if company_slug:
        company = get_object_or_404(Company, slug=company_slug)
    elif company_id:
        company = get_object_or_404(Company, id=company_id)
    else:
        return HttpResponseForbidden(_("Company not found."))
    
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden()

    logs = get_filtered_logs(request, company)
    output, error = export_as_pdf(logs)
    if error:
        return HttpResponse(error, status=400)
        
    response = HttpResponse(output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename=loglar_{company.name}_{timezone.now().date()}.pdf'
    return response

@login_required
def dashboard_export_zip(request, company_id=None, company_slug=None):
    if company_slug:
        company = get_object_or_404(Company, slug=company_slug)
    elif company_id:
        company = get_object_or_404(Company, id=company_id)
    else:
        return HttpResponseForbidden(_("Company not found."))
    
    if not (CompanyUser.objects.filter(user=request.user, company=company).exists() or request.user.is_superuser):
        return HttpResponseForbidden()
        
    logs = get_filtered_logs(request, company)
    output, error = export_as_zip(logs)
    if error:
        return HttpResponse(error, status=400)
        
    response = HttpResponse(output.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename=loglar_{company.name}_{timezone.now().date()}.zip'
    return response 