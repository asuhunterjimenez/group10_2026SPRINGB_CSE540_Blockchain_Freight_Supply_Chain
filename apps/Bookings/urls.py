from django.urls import path, include
from . import views
from django.contrib.auth.decorators import login_required, permission_required
urlpatterns = [
   path('booking_update_main_page/<str:request_id>/', login_required(views.BookingsView.make_booking), name='make_booking'),
   path('Payments/<int:booking_id>/',login_required(views.BookingsView.payments_booking_view), name='payments_booking'),
   path("apps/Payments/", include("apps.Payments.urls", namespace="Payments"))


   
]
