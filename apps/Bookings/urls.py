from django.urls import path, include
from . import views
from django.contrib.auth.decorators import login_required, permission_required
urlpatterns = [
   path('booking_update_main_page/<str:request_id>/', login_required(views.BookingsView.make_booking), name='make_booking'),
   path('Payments/<int:booking_id>/',login_required(views.BookingsView.payments_booking_view), name='payments_booking'),
   path("apps/Payments/", include("apps.Payments.urls", namespace="Payments")),
   path('booking_details/', login_required(views.BookingsView.booking_details), name='booking_details'),
   path('booking_approvals/', login_required(views.BookingsView.booking_approvals), name='booking_approvals'),
   path('booking_approvals_details/<int:id>/', login_required(views.BookingsView.booking_approvals_details), name='booking_approvals_details'),
   path('convert_booking_to_shipment/<int:request_id>/', login_required(views.BookingsView.convert_booking_to_shipment), name='convert_booking_to_shipment')
   


   
]
