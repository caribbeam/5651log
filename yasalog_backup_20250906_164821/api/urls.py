from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CompanyViewSet, LogKayitViewSet, CompanyUserViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'logs', LogKayitViewSet, basename='log')
router.register(r'users', CompanyUserViewSet, basename='companyuser')

urlpatterns = [
    path('v1/', include(router.urls)),
    path('v1/companies/<slug:company_slug>/logs/', LogKayitViewSet.as_view({'get': 'list', 'post': 'create'}), name='company-logs'),
    path('v1/companies/<slug:company_slug>/logs/statistics/', LogKayitViewSet.as_view({'get': 'statistics'}), name='company-logs-stats'),
    path('v1/companies/<slug:company_slug>/users/', CompanyUserViewSet.as_view({'get': 'list'}), name='company-users'),
]
