from django.test.runner import DiscoverRunner

class MyTestRunner(DiscoverRunner):
    def build_suite(self, test_labels=None, **kwargs):

        if not test_labels:
            test_labels = ["apps.Shipments.tests.test_tracking_views",
                           "apps.Payments.tests.test_payments_views",
                           "apps.Bookings.tests.test_bookings_views",
                           "apps.Quotings.tests.test_quotings_views",
                           "apps.Login.tests.test_login_views",
                           "apps.Home.tests.test_home_views"
                           ]

        return super().build_suite(test_labels, **kwargs)