from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import logout

class AutoLogoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = datetime.now()
            last_activity = request.session.get('last_activity')

            if last_activity:
                elapsed = now - datetime.fromisoformat(last_activity)
                if elapsed > timedelta(seconds=settings.SESSION_COOKIE_AGE):
                    logout(request)
                    request.session.flush()
            # Update last activity
            request.session['last_activity'] = now.isoformat()

        return self.get_response(request)
