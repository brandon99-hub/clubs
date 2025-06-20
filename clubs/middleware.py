# myproject/middleware.py
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

class CustomSessionCookieMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Check if the request path starts with '/admin'
        if request.path.startswith('/admin'):
            # Change the session cookie name for admin requests.
            if settings.SESSION_COOKIE_NAME in response.cookies:
                cookie = response.cookies.pop(settings.SESSION_COOKIE_NAME)
                response.cookies['admin_sessionid'] = cookie
        return response
