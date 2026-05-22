from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IPDAdmissionViewSet, VitalRecordViewSet

router = DefaultRouter()
router.register(r'ipd/admissions', IPDAdmissionViewSet, basename='ipd-admission')
router.register(r'ipd/vitals', VitalRecordViewSet, basename='ipd-vitals')

urlpatterns = [
    path('', include(router.urls)),
]
