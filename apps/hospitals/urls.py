from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HospitalViewSet, HospitalSelfView

router = DefaultRouter()
router.register(r'hospitals', HospitalViewSet, basename='hospital')

urlpatterns = [
    path('hospitals/me/', HospitalSelfView.as_view(), name='hospital-self'),
    path('', include(router.urls)),
]
