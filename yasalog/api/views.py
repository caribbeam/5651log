from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from log_kayit.models import Company, LogKayit, CompanyUser
from .serializers import CompanySerializer, LogKayitSerializer, CompanyUserSerializer
from django.utils import timezone

class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return Company.objects.all()
        return Company.objects.filter(users__user=self.request.user)

class LogKayitViewSet(viewsets.ModelViewSet):
    serializer_class = LogKayitSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        company_slug = self.kwargs.get('company_slug')
        if company_slug:
            company = get_object_or_404(Company, slug=company_slug)
            if self.request.user.is_superuser or CompanyUser.objects.filter(user=self.request.user, company=company).exists():
                return LogKayit.objects.filter(company=company)
        return LogKayit.objects.none()
    
    @action(detail=False, methods=['get'])
    def statistics(self, request, company_slug=None):
        """Şirket için istatistikler"""
        company = get_object_or_404(Company, slug=company_slug)
        logs = self.get_queryset()
        
        stats = {
            'total_logs': logs.count(),
            'today_logs': logs.filter(giris_zamani__date=timezone.now().date()).count(),
            'suspicious_logs': logs.filter(is_suspicious=True).count(),
            'unique_users': logs.values('ad_soyad').distinct().count(),
        }
        return Response(stats)

class CompanyUserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CompanyUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        company_slug = self.kwargs.get('company_slug')
        if company_slug:
            company = get_object_or_404(Company, slug=company_slug)
            if self.request.user.is_superuser or CompanyUser.objects.filter(user=self.request.user, company=company, role='admin').exists():
                return CompanyUser.objects.filter(company=company)
        return CompanyUser.objects.none()
