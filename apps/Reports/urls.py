from django.urls import path
from . import views

urlpatterns = [
    path('reports/', views.ReportsView.reports, name='reports'),
    path('reports/generate/', views.ReportsView.generate_report, name='generate_report'),
]