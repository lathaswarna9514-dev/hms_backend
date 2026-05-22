from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScheduleListView, ScheduleDetailView, ScheduleBookingInfoView, MySchedulesView, ShiftViewSet

router = DefaultRouter()
router.register('shifts', ShiftViewSet, basename='shift')

app_name = 'schedules'

urlpatterns = [
    path('', ScheduleListView.as_view(), name='schedule-list'),
    path('my/', MySchedulesView.as_view(), name='my-schedules'),
    path('<int:pk>/', ScheduleDetailView.as_view(), name='schedule-detail'),
    path('<int:pk>/booking-info/', ScheduleBookingInfoView.as_view(), name='schedule-booking-info'),
    path('', include(router.urls)),
]

