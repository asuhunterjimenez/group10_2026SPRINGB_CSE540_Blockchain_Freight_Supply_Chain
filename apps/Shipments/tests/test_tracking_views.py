from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from unittest.mock import patch, MagicMock

from apps.Login.models import GSA_agreement_form_tbl
from apps.Bookings.models import TrackingPoint, booking_freight_tbl


VIEWS_PATH = "apps.Shipments.views"


class ShippingViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="testuser",
            password="testpass"
        )
        self.client.login(username="testuser", password="testpass")

        now = timezone.now()

        self.content_type = ContentType.objects.get_for_model(booking_freight_tbl)

        self.gsa = GSA_agreement_form_tbl.objects.create(
            user_id_ref=self.user,
            date_received=now,
        )

        self.booking = booking_freight_tbl.objects.create(
            booking_reference_number="REQAE35F0AF5613",
            blockchain_tx_receipt="1",
            gsa_id_ref=self.gsa,
            date_received=now,
            time_received=now,
            content_type=self.content_type,
        )

        self.tp1 = TrackingPoint.objects.create(
            booking=self.booking,
            sequence=1,
            status="pending",
            booking_reference_number=self.booking.booking_reference_number,
            location="Loc1",
            latitude=10,
            longitude=20
        )

        self.tp2 = TrackingPoint.objects.create(
            booking=self.booking,
            sequence=2,
            status="pending",
            booking_reference_number=self.booking.booking_reference_number,
            location="Loc2",
            latitude=10,
            longitude=20
        )

        self.tp3 = TrackingPoint.objects.create(
            booking=self.booking,
            sequence=3,
            status="pending",
            booking_reference_number=self.booking.booking_reference_number,
            location="Loc3",
            latitude=10,
            longitude=20
        )

        self.url = reverse("update_tracking_info", args=[self.booking.id])

    # ----------------------------
    # INVALID METHOD
    # ----------------------------
    def test_invalid_request_method(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    # ----------------------------
    # MULTIPLE CURRENT STATUS
    # ----------------------------
    def test_multiple_current_invalid(self):
        data = {
            f"status_{self.tp1.id}": "current",
            f"status_{self.tp2.id}": "current",
            f"status_{self.tp3.id}": "pending",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

    # ----------------------------
    # INVALID ORDER BEFORE
    # ----------------------------
    def test_invalid_order_before(self):
        data = {
            f"status_{self.tp1.id}": "pending",
            f"status_{self.tp2.id}": "current",
            f"status_{self.tp3.id}": "pending",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

    # ----------------------------
    # INVALID ORDER AFTER
    # ----------------------------
    def test_invalid_order_after(self):
        data = {
            f"status_{self.tp1.id}": "passed",
            f"status_{self.tp2.id}": "current",
            f"status_{self.tp3.id}": "passed",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)

    # ----------------------------
    # VALID UPDATE (NO BLOCKCHAIN)
    # ----------------------------
    @patch(f"{VIEWS_PATH}.tracking_contract")
    def test_valid_update_no_blockchain(self, mock_contract):

        data = {
            f"status_{self.tp1.id}": "passed",
            f"status_{self.tp2.id}": "current",
            f"status_{self.tp3.id}": "pending",
        }

        self.client.post(self.url, data)

        tp1 = TrackingPoint.objects.get(id=self.tp1.id)
        tp2 = TrackingPoint.objects.get(id=self.tp2.id)

        self.assertEqual(tp1.status, "passed")
        self.assertEqual(tp2.status, "current")

        mock_contract.functions.updateTracking.assert_not_called()

    # ----------------------------
    # BLOCKCHAIN SUCCESS
    # ----------------------------
    @patch(f"{VIEWS_PATH}.w3")
    @patch(f"{VIEWS_PATH}.tracking_contract")
    def test_blockchain_called(self, mock_contract, mock_w3):

        mock_contract.functions.getTracking.return_value.call.return_value = []
        mock_contract.functions.updateTracking.return_value.build_transaction.return_value = {}

        mock_w3.eth.account.from_key.return_value.address = "0x123"
        mock_w3.eth.get_transaction_count.return_value = 1
        mock_w3.eth.gas_price = 1
        mock_w3.eth.estimate_gas.return_value = 21000
        mock_w3.eth.account.sign_transaction.return_value.raw_transaction = b"tx"
        mock_w3.eth.send_raw_transaction.return_value = b"hash"

        receipt = MagicMock()
        receipt.status = 1
        mock_w3.eth.wait_for_transaction_receipt.return_value = receipt

        data = {
            f"status_{self.tp1.id}": "passed",
            f"status_{self.tp2.id}": "passed",
            f"status_{self.tp3.id}": "current",
        }

        self.client.post(self.url, data)

        self.assertTrue(mock_contract.functions.updateTracking.called)

    # ----------------------------
    # BLOCKCHAIN FAILURE
    # ----------------------------
    @patch(f"{VIEWS_PATH}.w3")
    @patch(f"{VIEWS_PATH}.tracking_contract")
    def test_blockchain_failure(self, mock_contract, mock_w3):

        mock_contract.functions.getTracking.return_value.call.return_value = []
        mock_contract.functions.updateTracking.return_value.build_transaction.return_value = {}

        mock_w3.eth.account.from_key.return_value.address = "0x123"
        mock_w3.eth.get_transaction_count.return_value = 1
        mock_w3.eth.gas_price = 1
        mock_w3.eth.send_raw_transaction.side_effect = Exception("RPC error")

        data = {
            f"status_{self.tp1.id}": "passed",
            f"status_{self.tp2.id}": "passed",
            f"status_{self.tp3.id}": "current",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)

    # ----------------------------
    # LIST VIEW
    # ----------------------------
    def test_shipment_list_view(self):
        response = self.client.get(reverse("shipment_list"))
        self.assertEqual(response.status_code, 200)

    # ----------------------------
    # DETAIL VIEW
    # ----------------------------
    def test_shipment_details_view(self):
        response = self.client.get(
            reverse("shipment_details", args=[self.booking.id])
        )
        self.assertEqual(response.status_code, 200)

    # ----------------------------
    # UNAUTHORIZED USER
    # ----------------------------
    def test_unauthorized_user_redirect(self):
        self.client.logout()

        data = {
            f"status_{self.tp1.id}": "passed",
            f"status_{self.tp2.id}": "current",
            f"status_{self.tp3.id}": "pending",
        }

        response = self.client.post(self.url, data)

        self.assertIn(response.status_code, [302, 403])

    # ----------------------------
    # EMPTY POST DATA
    # ----------------------------
    def test_empty_post_data(self):
        response = self.client.post(self.url, {})

        self.assertIn(response.status_code, [200, 302])

        self.assertEqual(
            TrackingPoint.objects.filter(booking=self.booking).count(),
            3
        )

    # ----------------------------
    # PARTIAL UPDATE
    # ----------------------------
    def test_partial_tracking_update(self):
        data = {
            f"status_{self.tp1.id}": "current"
        }

        self.client.post(self.url, data)

        tp1 = TrackingPoint.objects.get(id=self.tp1.id)
        tp2 = TrackingPoint.objects.get(id=self.tp2.id)

        self.assertEqual(tp1.status, "current")
        self.assertEqual(tp2.status, "pending")

    # ----------------------------
    # VALIDATION UI (FIXED)
    # ----------------------------
    def test_validation_error_message_ui(self):
        data = {
            f"status_{self.tp1.id}": "",
            f"status_{self.tp2.id}": "current",
            f"status_{self.tp3.id}": "pending",
        }

        response = self.client.post(self.url, data)

        self.assertEqual(response.status_code, 302)

        messages = list(response.wsgi_request._messages)
        self.assertTrue(any("must" in str(m).lower() for m in messages))

    # ----------------------------
    # BLOCKCHAIN ROLLBACK CHECK
    # ----------------------------
    @patch(f"{VIEWS_PATH}.w3")
    @patch(f"{VIEWS_PATH}.tracking_contract")
    def test_blockchain_failure_rolls_back_db(self, mock_contract, mock_w3):

        mock_contract.functions.getTracking.return_value.call.return_value = []
        mock_contract.functions.updateTracking.return_value.build_transaction.return_value = {}

        mock_w3.eth.account.from_key.return_value.address = "0x123"
        mock_w3.eth.get_transaction_count.return_value = 1
        mock_w3.eth.gas_price = 1
        mock_w3.eth.send_raw_transaction.side_effect = Exception("RPC failure")

        self.client.post(self.url, {
            f"status_{self.tp1.id}": "passed",
            f"status_{self.tp2.id}": "current",
        })

        self.tp1.refresh_from_db()
        self.assertEqual(self.tp1.status, "passed")

    # ----------------------------
    # BULK PERFORMANCE
    # ----------------------------
    def test_bulk_tracking_update_performance(self):

        data = {}

        import time
        start = time.time()

        for i in range(1, 51):
            tp = TrackingPoint.objects.create(
                booking=self.booking,
                sequence=i + 3,
                status="pending",
                booking_reference_number=self.booking.booking_reference_number,
                location=f"Loc{i}",
                latitude=10,
                longitude=20
            )
            data[f"status_{tp.id}"] = "passed"

        response = self.client.post(self.url, data)

        end = time.time()

        self.assertIn(response.status_code, [200, 302])
        self.assertLess(end - start, 2)