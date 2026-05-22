from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LabTestViewSet, LabRequestViewSet

router = DefaultRouter()
router.register(r'lab/tests', LabTestViewSet, basename='lab-test')
router.register(r'lab/requests', LabRequestViewSet, basename='lab-request')

urlpatterns = [
    path('', include(router.urls)),
]
