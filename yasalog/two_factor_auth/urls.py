from django.urls import path
from . import views

app_name = 'two_factor_auth'

urlpatterns = [
    path('setup/<slug:company_slug>/', views.setup_2fa, name='setup'),
    path('verify/', views.verify_2fa, name='verify'),
    path('dashboard/<slug:company_slug>/', views.dashboard_2fa, name='dashboard'),
    path('settings/<slug:company_slug>/', views.settings_2fa, name='settings'),
    path('logs/<slug:company_slug>/', views.logs_2fa, name='logs'),
]
