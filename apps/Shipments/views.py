from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings

from web3 import Web3
import os
import json

from apps.Login.models import (
    GSA_agreement_form_tbl,
    ocean_freight_tbl,
    air_freight_tbl,
    roro_tbl,
    customs_brokerage_tbl,
)

from apps.Bookings.models import booking_freight_tbl, vehicle, goods, TrackingPoint
from apps.Payments.models import blockchain_payment
from django.db import transaction


# ---------------------------------------------------
# BLOCKCHAIN SETUP
# ---------------------------------------------------
w3 = Web3(Web3.HTTPProvider(settings.GANACHE_URL))

TRACKING_CONTRACT_ADDRESS = Web3.to_checksum_address(
    settings.TRACKING_CONTRACT_ADDRESS
)

ABI_PATH = os.path.join(settings.BASE_DIR, settings.TRACKING_CONTRACT_ABI)

with open(ABI_PATH, "r") as f:
    TRACKING_CONTRACT_ABI = json.load(f)["abi"]

tracking_contract = w3.eth.contract(
    address=TRACKING_CONTRACT_ADDRESS,
    abi=TRACKING_CONTRACT_ABI
)


# ---------------------------------------------------
# SHIPPING VIEW CLASS
# ---------------------------------------------------
class shippingView:

    # ===================================================
    # SHIPMENT LIST
    # ===================================================
    @staticmethod
    def shipment_list(request):

        gsa_user = GSA_agreement_form_tbl.objects.filter(
            username=request.user.username
        ).first()

        base_query = booking_freight_tbl.objects.exclude(
            blockchain_tx_receipt='0'
        ).order_by("-id")

        if request.user.is_staff:
            shipments = base_query

        elif request.user.groups.filter(name="ware_house").exists():
            shipments = base_query

            for shipment in shipments:
                last_tracking = TrackingPoint.objects.filter(
                    booking_reference_number=shipment.booking_reference_number
                ).order_by("-sequence").first()

                shipment.is_current = (
                    last_tracking.status == "current"
                    if last_tracking else False
                )

        else:
            shipments = base_query.filter(
                gsa_id_ref_id=gsa_user.id if gsa_user else None
            )

        return render(request, "Shipments/shipment_list.html", {
            "shipments": shipments,
            "user_groups": list(request.user.groups.values_list("name", flat=True))
        })


    # ===================================================
    # SHIPMENT DETAILS
    # ===================================================
    @staticmethod
    def shipment_details(request, id):

        booking = get_object_or_404(booking_freight_tbl, id=id)

        shipper_details = booking.gsa_id_ref
        shipper_fullname = shipper_details.user_id_ref.get_full_name()

        # Resolve freight type
        air = air_freight_tbl.objects.filter(
            request_id=booking.quote_reference_number
        ).first() if booking.content_type.model == 'air_freight_tbl' else None

        ocean = ocean_freight_tbl.objects.filter(
            request_id=booking.quote_reference_number
        ).first() if booking.content_type.model == 'ocean_freight_tbl' else None

        roro = roro_tbl.objects.filter(
            request_id=booking.quote_reference_number
        ).first() if booking.content_type.model == 'roro_tbl' else None

        customs = customs_brokerage_tbl.objects.filter(
            quote_request_id=booking.quote_reference_number
        ).first() if booking.content_type.model == 'customs_brokerage_tbl' else None

        customer_quoting_details = air or ocean or roro or customs

        blockchain_payment_details = blockchain_payment.objects.filter(
            quote_request_id=booking.quote_reference_number
        ).first()

        tracking_info = TrackingPoint.objects.filter(
            booking_id=booking.id
        ).order_by("sequence")

        # File handling
        username = booking.gsa_id_ref.username
        folder_path = os.path.join(settings.MEDIA_ROOT, "uploads", username)

        files = []
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                files.append({
                    "name": filename,
                    "url": f"{settings.MEDIA_URL}uploads/{username}/{filename}"
                })

        vehicles = vehicle.objects.filter(booking_id_ref=booking.id)
        goods_list = goods.objects.filter(booking_id_ref=booking.id)

        return render(request, "Shipments/shipment_tracking_list.html", {
            "booking": booking,
            "request_id": booking.id,

            # Shipper
            "shipper_details": shipper_details,
            "shipper_company_name": shipper_details.customer_registered_business_name,
            "shipper_fullname": shipper_fullname,
            "shipper_address": shipper_details.service_address,
            "shipper_export_number": shipper_details.corp_jur_number,
            "shipper_phone_number": shipper_details.telephone_number,
            "shipper_email": shipper_details.email_address,

            # Receiver
            "receiver_company_name": booking.receiver_company_name,
            "receiver_fullname": booking.receiver_fullname,
            "date_received": booking.date_received,
            "time_received": booking.time_received,
            "receiver_phone_number": booking.receiver_phone_number,
            "receiver_email": booking.receiver_email,
            "receiver_tax_id": booking.receiver_tax_id,
            "receiver_driver_lincence_number": booking.receiver_driver_lincence_number,
            "receiver_passport_no": booking.receiver_passport_no,
            "receiver_address": booking.receiver_address,

            # Freight
            "service_type": booking.service_type,
            "quote_reference_number": booking.quote_reference_number,
            "request_status": booking.request_status,

            "air": air,
            "ocean": ocean,
            "roro": roro,
            "customs": customs,
            "customer_quoting_details": customer_quoting_details,

            # Blockchain
            "blockchain_payment_details": blockchain_payment_details,

            # Files
            "files": files,

            # Logistics
            "vehicles": vehicles,
            "goods": goods_list,
            "tracking_info": tracking_info,
        })


    # ===================================================
    # UPDATE TRACKING (DB FIRST → BLOCKCHAIN)
    # ===================================================
    @staticmethod
    @login_required
    def update_tracking_info(request, request_id):

        if request.method != "POST":
            messages.error(request, "Invalid request method.")
            return redirect("shipment_list")

        # ---------------------------------------------------
        # FETCH TRACKING DATA
        # ---------------------------------------------------
        tracking_points = list(
            TrackingPoint.objects.filter(
                booking_id=request_id
            ).order_by("sequence")
        )

        if not tracking_points:
            messages.error(request, "No tracking data found.")
            return redirect("shipment_list")

        # ---------------------------------------------------
        # APPLY FORM UPDATES
        # ---------------------------------------------------
        updates = {}

        for key, value in request.POST.items():
            if key.startswith("status_"):
                try:
                    tracking_id = int(key.split("_")[1])
                    updates[tracking_id] = value.strip().lower()
                except:
                    continue

        for tp in tracking_points:
            if tp.id in updates:
                tp.status = updates[tp.id]

        # ---------------------------------------------------
        # VALIDATION RULES
        # ---------------------------------------------------
        statuses = [tp.status for tp in tracking_points]

        if statuses.count("current") != 1:
            messages.error(request, "Must have exactly one 'current'.")
            return redirect("shipment_list")

        current_index = statuses.index("current")

        if any(s != "passed" for s in statuses[:current_index]):
            messages.error(request, "All previous must be 'passed'.")
            return redirect("shipment_list")

        if any(s != "pending" for s in statuses[current_index + 1:]):
            messages.error(request, "All next must be 'pending'.")
            return redirect("shipment_list")

        # ---------------------------------------------------
        # SAVE + BLOCKCHAIN (ATOMIC FIX ADDED ONLY HERE)
        # ---------------------------------------------------
        try:
            with transaction.atomic():

                # SAVE DATABASE (SOURCE OF TRUTH)
                for tp in tracking_points:
                    tp.save()

                # ---------------------------------------------------
                # BLOCKCHAIN SYNC (LAST POINT ONLY)
                # ---------------------------------------------------
                try:
                    account = w3.eth.account.from_key(settings.GANACHE_PRIVATE_KEY)

                    status_map = {
                        "pending": 0,
                        "current": 1,
                        "passed": 2
                    }

                    last_tp = tracking_points[-1]

                    # Only push meaningful forward step
                    if last_tp.status.strip().lower() != "current":
                        messages.info(request, "No blockchain update needed (not advancing step).")
                        messages.success(request, "Off-chain updated successfully.")
                        return redirect("shipment_list")

                    # Get sequence from blockchain
                    onchain_data = tracking_contract.functions.getTracking(
                        last_tp.booking_reference_number
                    ).call()

                    new_sequence = len(onchain_data) + 1

                    txn = tracking_contract.functions.updateTracking(
                        last_tp.booking_reference_number,
                        last_tp.location,
                        new_sequence,
                        status_map[last_tp.status.strip().lower()],
                        int(last_tp.latitude),
                        int(last_tp.longitude),
                        int(last_tp.arrival_time.timestamp()) if last_tp.arrival_time else 0,
                        int(last_tp.departure_time.timestamp()) if last_tp.departure_time else 0,
                    ).build_transaction({
                        "from": account.address,
                        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
                        "gasPrice": w3.eth.gas_price,
                    })

                    try:
                        txn["gas"] = w3.eth.estimate_gas(txn)
                    except:
                        txn["gas"] = 800000

                    signed_tx = w3.eth.account.sign_transaction(
                        txn,
                        settings.GANACHE_PRIVATE_KEY
                    )

                    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                    if receipt.status == 1:
                        messages.success(request, "Blockchain sync successful.")
                        messages.info(request, f"TX Hash: {w3.to_hex(tx_hash)}")
                    else:
                        messages.error(request, "Blockchain transaction failed.")
                        raise Exception("Blockchain transaction failed")

                except Exception as e:
                    messages.error(request, f"Blockchain error: {str(e)}")
                    raise   # triggers rollback

        # ---------------------------------------------------
        # FINAL RESPONSE
        # ---------------------------------------------------
        except Exception:
            return redirect("shipment_list")

        messages.success(request, "Tracking updated successfully.")
        return redirect("shipment_list")