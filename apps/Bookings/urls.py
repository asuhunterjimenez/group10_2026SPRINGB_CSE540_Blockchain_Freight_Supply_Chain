from django.urls import path, include
from . import views
from django.contrib.auth.decorators import login_required, permission_required
urlpatterns = [
   #path('booking_update_main_page/<str:id>/', login_required(views.BookingsView.view_booking), name='view_booking'),
   path('Payments/<int:request_id>/',login_required(views.BookingsView.payments_booking_view), name='payments_booking'),
   path("apps/Payments/", include("apps.Payments.urls", namespace="Payments")),
   path('booking_details/', login_required(views.BookingsView.booking_details), name='booking_details')


   
]
