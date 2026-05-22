from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DoctorListView, DoctorDetailView, SpecialtyListView, LeaveRequestViewSet

router = DefaultRouter()
router.register('leaves', LeaveRequestViewSet, basename='leave')

app_name = 'doctors'

urlpatterns = [
    path('', DoctorListView.as_view(), name='doctor-list'),
    path('<int:pk>/', DoctorDetailView.as_view(), name='doctor-detail'),
    path('specialties/', SpecialtyListView.as_view(), name='specialty-list'),
    path('', include(router.urls)),
]
