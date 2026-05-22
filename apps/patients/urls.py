from django.urls import path
from .views import PatientListView, PatientDetailView, PatientProfileView, PatientHistoryView, PatientHistoryDetailView

app_name = 'patients'

urlpatterns = [
    path('', PatientListView.as_view(), name='patient-list'),
    path('me/', PatientProfileView.as_view(), name='patient-me'),
    path('me/history/', PatientHistoryView.as_view(), name='patient-history'),
    path('<int:pk>/', PatientDetailView.as_view(), name='patient-detail'),
    path('<int:pk>/history/', PatientHistoryDetailView.as_view(), name='patient-history-detail'),
]
