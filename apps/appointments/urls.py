from django.urls import path
from .views import (
    AppointmentListView, AppointmentDetailView,
    BookAppointmentView, MyAppointmentsView,
    DoctorAppointmentsView, FrontDeskBookView
)

app_name = 'appointments'

urlpatterns = [
    path('', AppointmentListView.as_view(), name='appointment-list'),
    path('book/', BookAppointmentView.as_view(), name='book-appointment'),
    path('offline-book/', FrontDeskBookView.as_view(), name='offline-book'),
    path('my/', MyAppointmentsView.as_view(), name='my-appointments'),
    path('doctor/', DoctorAppointmentsView.as_view(), name='doctor-appointments'),
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
]
