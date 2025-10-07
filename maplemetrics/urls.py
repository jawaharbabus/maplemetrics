"""
URL configuration for maplemetrics project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.views.generic import TemplateView

def api_root(request):
    """Root API endpoint with available endpoints."""
    return JsonResponse({
        'message': 'MapleMetrics Financial Agent API',
        'version': '1.0',
        'endpoints': {
            'health': '/api/agent/health/',
            'query': '/api/agent/query/',
            'structured_query': '/api/agent/query/structured/',
            'admin': '/admin/',
        }
    })

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('api/', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('api/agent/', include('agent.urls')),
]
