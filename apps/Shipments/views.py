from django.contrib.auth.decorators import login_required
from apps.Helpers.decorators import group_required
from django.shortcuts import render, redirect
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from django.core.mail import send_mail
from apps.Login.models import (
    GSA_agreement_form_tbl,
    ocean_freight_tbl,
    air_freight_tbl,
    roro_tbl,
    customs_brokerage_tbl,
    new_quotings
)
from apps.Bookings.models import booking_freight_tbl, vehicle, goods
from apps.Payments.models import blockchain_payment
from django.contrib.contenttypes.models import ContentType
import json
import datetime
from datetime import datetime
from web3 import Web3

#for image access
import os
from django.http import JsonResponse


class shippingView:
 
    
    @staticmethod
    def shipment_list(request):
        gsa_user = GSA_agreement_form_tbl.objects.filter(
            username=request.user.username
        ).first()

        if request.user.is_staff:
            shipments = booking_freight_tbl.objects.exclude(
                blockchain_tx_receipt='0'
            ).order_by("-id")
        else:
            shipments = booking_freight_tbl.objects.filter(
                gsa_id_ref_id=gsa_user.id
            ).exclude(
                blockchain_tx_receipt='0'
            ).order_by("-id")

        context = {
            "shipments": shipments,
        }

        return render(request, "Shipments/shipment_list.html", context)
        
    @staticmethod
    def shipment_details(request, id):
        booking = booking_freight_tbl.objects.get(id=id)
        return render(request, "Shipments/shipment_details.html", {"booking": booking})