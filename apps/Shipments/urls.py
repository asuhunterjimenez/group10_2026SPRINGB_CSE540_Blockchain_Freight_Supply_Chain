from django.urls import path
from . import views

urlpatterns = [
    path('shipment/', views.shippingView.shipment_list, name='shipment_list'),
    path('shipment/details/<int:id>/', views.shippingView.shipment_details, name='shipment_details'),
    #path('shipment/update_tracking_info/<int:id>/', views.shippingView.update_tracking_info, name='update_tracking_info'),
    path(
    'apps/Shipments/shipment/update_tracking_info/<int:request_id>/',
    views.shippingView.update_tracking_info,
    name='update_tracking_info'
)
    #path('shipment/<int:id>/', views.shippingView.shipment_list, name='shipment_list')
]