from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.contrib.contenttypes.models import ContentType
from apps.Bookings.models import goods, booking_freight_tbl
from apps.Login.models import GSA_agreement_form_tbl
from apps.Payments.models import blockchain_payment
from django.utils import timezone


class BookingViewsTests(TestCase):

    def setUp(self):
        self.client = Client()

        # -------------------------
        # USER
        # -------------------------
        self.user = User.objects.create_user(
            username="testuser",
            password="pass123",
            email="test@mail.com",
            first_name="Geoffrey",
            last_name="Kasibante"
        )

        # IMPORTANT: correct group for our views
        self.user.groups.clear()

        sales_group, _ = Group.objects.get_or_create(name="sales_team")
        self.user.groups.add(sales_group)

        self.client.login(username="testuser", password="pass123")

        # -------------------------
        # GSA AGREEMENT
        # -------------------------
        self.gsa = GSA_agreement_form_tbl.objects.create(
            username=self.user,
            user_id_ref=self.user,
            date_received=timezone.now().date(),
            customer_registered_business_name="Test Company",
            service_address="Test Address",
            corp_jur_number="123456",
            telephone_number="1234567890",
            email_address="test@mail.com"
        )

        # -------------------------
        # BOOKING
        # -------------------------
        content_type = ContentType.objects.get_for_model(goods)

        self.booking = booking_freight_tbl.objects.create(
            date_received=timezone.now().date(),
            time_received=timezone.now().time(),

            service_type="Air Freight",
            receiver_company_name="Twinkle Pharmaceuticals",
            receiver_fullname="Twinkle Partel",
            receiver_phone_number="123456789",
            receiver_email="receiver@mail.com",
            receiver_address="Some Address",

            quote_reference_number="Q123",
            booking_reference_number="B123",

            gsa_id_ref=self.gsa,
            content_type=content_type,
            object_id=1
        )

    # =========================================================
    # PAYMENTS VIEW SUCCESS
    # =========================================================
    @patch("apps.Bookings.views.ocean_freight_tbl")
    def test_payments_booking_view_success(self, mock_ocean):
        mock_ocean.objects.get.return_value = MagicMock(total_charges=500)

        response = self.client.get(
            reverse("payments_booking", kwargs={"booking_id": self.booking.id})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Air Freight")

    # =========================================================
    # PAYMENTS VIEW NOT FOUND
    # =========================================================
    def test_payments_booking_view_not_found(self):
        response = self.client.get(
            reverse("payments_booking", kwargs={"booking_id": 999})
        )

        self.assertEqual(response.status_code, 302)

    # =========================================================
    # BOOKING DETAILS VIEW
    # =========================================================
    def test_booking_details_view(self):
        blockchain_payment.objects.create(
            quote_request_id="Q123",
            paid_amount=100
        )

        response = self.client.get(reverse("booking_details"))

        self.assertEqual(response.status_code, 200)

    # =========================================================
    # BOOKING APPROVALS VIEW
    # =========================================================
    def test_booking_approvals_view(self):
        blockchain_payment.objects.create(
            quote_request_id="Q123",
            paid_amount=100
        )

        response = self.client.get(reverse("booking_approvals"))

        self.assertEqual(response.status_code, 200)

    # =========================================================
    # APPROVAL DETAILS NOT FOUND
    # =========================================================
    def test_booking_approvals_details_not_found(self):
        response = self.client.get(
            reverse("booking_approvals_details", args=[999]),
            follow=True
        )

        self.assertRedirects(response, reverse("booking_approvals"))

    # =========================================================
    # CONVERT BOOKING SUCCESS
    # =========================================================
    @patch("apps.Bookings.views.Web3")
    @patch("apps.Bookings.views.send_mail")
    @patch("apps.Bookings.views.open")
    def test_convert_booking_success(self, mock_open, mock_mail, mock_web3):

        mock_w3 = MagicMock()
        mock_web3.return_value = mock_w3
        mock_w3.is_connected.return_value = True
        mock_w3.eth.accounts = ["0xabc"]

        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        mock_tx_receipt = MagicMock()
        mock_tx_receipt.transactionHash.hex.return_value = "0xhash"
        mock_tx_receipt.blockNumber = 1

        mock_w3.eth.wait_for_transaction_receipt.return_value = mock_tx_receipt

        mock_contract.functions.createShipment.return_value.transact.return_value = "tx"

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        response = self.client.post(
            reverse("convert_booking_to_shipment", args=[self.booking.id]),
            {
                "service_type": "Air Freight",
                "shipper_fullname": "Samuel Katende",
                "receiver_fullname": "Twinkle Partel",
                "quote_reference_number": "Q123",
                "departure": "CAYVR VANCOUVER",
                "destination": "nigeria",
                "air_departure_country": "canada",
                "air_destination_country": "nigeria",
                "paid_amount": "1"
            }
        )

        self.assertEqual(response.status_code, 302)

    # =========================================================
    # CONVERT BOOKING INVALID METHOD
    # =========================================================
    def test_convert_booking_invalid_method(self):
        response = self.client.get(
            reverse("convert_booking_to_shipment", args=[self.booking.id]),
            follow=True
        )

        self.assertRedirects(response, reverse("booking_approvals"))

    # =========================================================
    # TRACK SHIPMENT SUCCESS
    # =========================================================
    @patch("apps.Bookings.views.Web3")
    @patch("apps.Bookings.views.open")
    def test_track_shipment_success(self, mock_open, mock_web3):

        mock_w3 = MagicMock()
        mock_web3.return_value = mock_w3
        mock_w3.is_connected.return_value = True

        mock_contract = MagicMock()
        mock_w3.eth.contract.return_value = mock_contract

        mock_contract.functions.shipments.return_value.call.return_value = [0] * 8
        mock_contract.functions.parties.return_value.call.return_value = []

        mock_open.return_value.__enter__.return_value.read.return_value = "[]"

        response = self.client.get(
            reverse("track_shipment", args=[self.booking.id])
        )

        self.assertEqual(response.status_code, 200)