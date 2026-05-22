from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RoomViewSet, BedViewSet

router = DefaultRouter()
router.register(r'rooms', RoomViewSet, basename='room')
router.register(r'beds', BedViewSet, basename='bed')

urlpatterns = [
    path('', include(router.urls)),
]
