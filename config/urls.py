"""
eDoc HMS - URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root_view(request):
    return JsonResponse({
        "status": "online",
        "message": "eDoc HMS API is running successfully on Vercel!",
        "version": "1.0.0"
    })

urlpatterns = [
    path('', api_root_view, name='api-root'),
    path('admin/', admin.site.urls),

    # API Routes
    path('api/auth/', include('authentication.urls')),
    path('api/doctors/', include('doctors.urls')),
    path('api/patients/', include('patients.urls')),
    path('api/appointments/', include('appointments.urls')),
    path('api/schedules/', include('schedules.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/common/', include('common.urls')),
    path('api/', include('hospitals.urls')),
    path('api/', include('support.urls')),
    path('api/', include('departments.urls')),
    path('api/', include('rooms_beds.urls')),
    path('api/', include('ipd.urls')),
    path('api/', include('pharmacy.urls')),
    path('api/', include('lab.urls')),
    path('api/billing/', include('billing.urls')),
    path('api/opd/', include('opd.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
