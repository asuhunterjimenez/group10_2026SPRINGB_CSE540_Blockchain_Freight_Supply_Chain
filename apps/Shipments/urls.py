from django.urls import path
from . import views

urlpatterns = [
    path('shipment/', views.shippingView.shipment_list, name='shipment_list'),
    path('shipment/details/<int:id>/', views.shippingView.shipment_details, name='shipment_details'),
]