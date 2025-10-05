"""
URL configuration for agent app.
"""
from django.urls import path
from . import views

app_name = 'agent'

urlpatterns = [
    path('', views.HealthCheckView.as_view(), name='index'),
    path('query/', views.AgentQueryView.as_view(), name='query'),
    path('query/structured/', views.AgentStructuredQueryView.as_view(), name='query_structured'),
    path('health/', views.HealthCheckView.as_view(), name='health'),
]
