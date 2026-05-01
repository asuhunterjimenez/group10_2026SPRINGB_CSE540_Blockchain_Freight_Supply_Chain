from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User, Group
from django.urls import reverse
from django.utils import timezone

from apps.Login.models import (
    ocean_freight_tbl,
    air_freight_tbl,
    roro_tbl,
    customs_brokerage_tbl,
    GSA_agreement_form_tbl,
)

# ===========================
# HELPERS
# ===========================
def add_group(user, name):
    group, _ = Group.objects.get_or_create(name=name)
    user.groups.add(group)
    user.save()


# ===========================
# TEST CASE
# ===========================
@override_settings(USE_TZ=True)
class HomeViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        # ---------------- USER ----------------
        self.user = User.objects.create_user(
            username="testuser",
            password="pass123",
            email="test@mail.com"
        )

        add_group(self.user, "clients_team")

        self.client.login(username="testuser", password="pass123")

        # ---------------- GSA ----------------
        self.gsa = GSA_agreement_form_tbl.objects.create(
            user_id_ref=self.user,
            username=self.user.username,
            date_received=timezone.now().date(),
            customer_registered_business_name="Test Company",
            service_address="Test Address",
            corp_jur_number="123",
            telephone_number="123",
            email_address="test@mail.com",
            locked_by="0"
        )

        now = timezone.now()

        # ---------------- OCEAN ----------------
        self.ocean = ocean_freight_tbl.objects.create(
            request_id="REQ1",
            id_gsa_ref=self.gsa,
            date_received=now.date(),
            time_received=now.time(),
            updated_date_time=now,
            request_status="Draft"
        )

        # ---------------- AIR ----------------
        self.air = air_freight_tbl.objects.create(
            request_id="REQ2",
            id_gsa_ref=self.gsa,
            date_received=now.date(),
            time_received=now.time(),
            updated_date_time=now,
            request_status="Approved Quote"
        )

        # ---------------- RORO ----------------
        self.roro = roro_tbl.objects.create(
            request_id="REQ3",
            id_gsa_ref=self.gsa,
            date_received=now.date(),
            time_received=now.time(),
            updated_date_time=now,
            request_status="Rejected Quote"
        )

        # ---------------- CUSTOMS ----------------
        self.customs = customs_brokerage_tbl.objects.create(
            request_id="REQ4",
            id_gsa_ref=self.gsa,
            date_received=now.date(),
            time_received=now.time(),
            updated_date_time=now,
            request_status="Draft"
        )

    # ===========================
    # 1. DASHBOARD LOADS
    # ===========================
    def test_dashboard_loads(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "Home/dashboard.html")

    # ===========================
    # 2. CONTEXT KEYS EXIST
    # ===========================
    def test_dashboard_context_keys(self):
        response = self.client.get(reverse("dashboard"))

        self.assertIn("ocean_data", response.context)
        self.assertIn("air_data", response.context)
        self.assertIn("roro_data", response.context)
        self.assertIn("customs_data", response.context)

        self.assertIn("total_pending", response.context)
        self.assertIn("total_accepted_monthly", response.context)
        self.assertIn("total_rejected_monthly", response.context)

    # ===========================
    # 3. TOTAL PENDING LOGIC
    # ===========================
    def test_total_pending_calculation(self):
        response = self.client.get(reverse("dashboard"))

        total_pending = response.context["total_pending"]

        # we created:
        # ocean Draft = 1
        # customs Draft = 1
        # air + roro = not Draft
        self.assertEqual(total_pending, 2)

    # ===========================
    # 4. ACCEPTED COUNT
    # ===========================
    def test_total_accepted_monthly(self):
        response = self.client.get(reverse("dashboard"))

        total_accepted = response.context["total_accepted_monthly"]

        # only air is "Approved Quote"
        self.assertEqual(total_accepted, 1)

    # ===========================
    # 5. REJECTED COUNT
    # ===========================
    def test_total_rejected_monthly(self):
        response = self.client.get(reverse("dashboard"))

        total_rejected = response.context["total_rejected_monthly"]

        # only roro is "Rejected Quote"
        self.assertEqual(total_rejected, 1)

    # ===========================
    # 6. LOGIN REQUIRED
    # ===========================
    def test_dashboard_requires_login(self):
        self.client.logout()

        response = self.client.get(reverse("dashboard"))

        # login_required decorator
        self.assertIn(response.status_code, [302, 403])