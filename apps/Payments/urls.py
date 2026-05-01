# apps/Payments/urls.py
from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("create/", views.create_blockchain_payment, name="create_blockchain_payment"),
    path("success/", views.payment_success, name="success"),
    path("cancel/", views.payment_cancel, name="cancel"),
    path("balance/", views.payment_balance_list, name="payment_balance_list"),
    path("update_blockchain_payment/<int:id>/", views.update_blockchain_payment, name="update_blockchain_payment"),
]