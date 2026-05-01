from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User, Group
from django.urls import reverse, NoReverseMatch
from django.contrib.auth.models import Group
from unittest.mock import patch
from django.core import mail


# ===========================
# HELPERS
# ===========================
def add_group(user, name):
    group, _ = Group.objects.get_or_create(name=name)
    user.groups.add(group)
    user.save()


def safe_reverse(name):
    """
    Prevent test crash if URL name doesn't exist
    """
    try:
        return reverse(name)
    except NoReverseMatch:
        return None


# ===========================
# TEST CASE
# ===========================
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class LoginViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        #  id = 3 to exist
        Group.objects.all().delete()

        group = Group.objects.create(id=3, name="clients_team")

        self.user = User.objects.create_user(
            username="testuser",
            password="pass123",
            email="test@mail.com"
        )

        self.user.groups.add(group)
        self.user.save()

    # ===========================
    # LOGIN SUCCESS
    # ===========================
    def test_login_success(self):
        url = safe_reverse("login")
        self.assertIsNotNone(url)

        response = self.client.post(url, {
            "username": "testuser",
            "password": "pass123"
        })

        self.assertIn(response.status_code, [200, 302])

    # ===========================
    # LOGIN FAIL
    # ===========================
    def test_login_invalid_credentials(self):
        url = safe_reverse("login")
        self.assertIsNotNone(url)

        response = self.client.post(url, {
            "username": "wrong",
            "password": "wrong"
        })

        self.assertEqual(response.status_code, 200)

    # ===========================
    # EMPTY LOGIN
    # ===========================
    def test_login_empty_fields(self):
        url = safe_reverse("login")
        self.assertIsNotNone(url)

        response = self.client.post(url, {
            "username": "",
            "password": ""
        })

        self.assertEqual(response.status_code, 200)

    # ===========================
    # LOGOUT
    # ===========================
    def test_logout(self):
        self.client.login(username="testuser", password="pass123")

        url = safe_reverse("pagelogout")

        # fallback if URL name differs
        if url is None:
            url = safe_reverse("logout")

        self.assertIsNotNone(url, "Logout URL not found in urls.py")

        response = self.client.get(url)

        self.assertIn(response.status_code, [200, 302])

    # ===========================
    # DASHBOARD
    # ===========================
    def test_dashboard_access(self):
        self.client.login(username="testuser", password="pass123")

        url = safe_reverse("dashboard")
        self.assertIsNotNone(url)

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    # ===========================
    # FORGOT PASSWORD
    # ===========================
    @patch("apps.Login.views.send_mail")
    def test_forgot_password_success(self, mock_send_mail):
        url = safe_reverse("forgot_password")
        self.assertIsNotNone(url)

        response = self.client.post(url, {
            "client_email": "test@mail.com"
        })

        self.assertIn(response.status_code, [200, 302])
        mock_send_mail.assert_called_once()

    # ===========================
    # INVALID EMAIL
    # ===========================
    def test_forgot_password_invalid_email(self):
        url = safe_reverse("forgot_password")
        self.assertIsNotNone(url)

        response = self.client.post(url, {
            "client_email": "notexists@mail.com"
        })

        self.assertEqual(response.status_code, 302)

    # ===========================
    # CREATE USER SUCCESS
    # ===========================
    @patch("apps.Login.views.send_mail")
    def test_create_user_success(self, mock_send_mail):
        # ensure group exists instead of group_id=3
        Group.objects.get_or_create(name="clients_team")

        url = safe_reverse("Create_client_user")
        self.assertIsNotNone(url)

        response = self.client.post(url, {
            "first_name": "John",
            "second_name": "Doe",
            "username": "johndoe",
            "email": "john@mail.com",
            "password": "secret123"
        })

        self.assertIn(response.status_code, [200, 302])
        self.assertTrue(User.objects.filter(username="johndoe").exists())
        mock_send_mail.assert_called_once()

    # ===========================
    # CREATE USER FAIL
    # ===========================
    def test_create_user_validation_fail(self):
        url = safe_reverse("Create_client_user")
        self.assertIsNotNone(url)

        response = self.client.post(url, {
            "first_name": "",
            "second_name": "",
            "username": "abc",
            "email": "bad",
            "password": "1"
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(username="abc").exists())