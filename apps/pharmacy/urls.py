from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MedicineCategoryViewSet, MedicineViewSet, DispenseOrderViewSet

router = DefaultRouter()
router.register(r'pharmacy/categories', MedicineCategoryViewSet, basename='pharma-category')
router.register(r'pharmacy/medicines', MedicineViewSet, basename='pharma-medicine')
router.register(r'pharmacy/orders', DispenseOrderViewSet, basename='pharma-order')

urlpatterns = [
    path('', include(router.urls)),
]
