from django.urls import path
from .views import (
    InvoiceListView, InvoiceDetailView,
    CompileIPDInvoiceView, MyInvoicesView
)

app_name = 'billing'

urlpatterns = [
    path('invoices/', InvoiceListView.as_view(), name='invoice-list'),
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),
    path('invoices/<int:pk>/pay/', InvoiceDetailView.as_view(), name='invoice-pay'),
    path('invoices/compile-ipd/', CompileIPDInvoiceView.as_view(), name='invoice-compile-ipd'),
    path('my-invoices/', MyInvoicesView.as_view(), name='my-invoices'),
]
