from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


class BotServiceUser:

    is_authenticated = True
    is_anonymous = False
    role = "bot"
    id = None
    pk = None


class BotTokenAuthentication(BaseAuthentication):

    def authenticate(self, request):
        token = request.headers.get("X-Bot-Token")
        expected = getattr(settings, "BOT_API_TOKEN", "")
        if not expected:
            return None
        if token != expected:
            raise AuthenticationFailed("Yaroqsiz bot tokeni.")
        return (BotServiceUser(), None)


class IsBotToken(BasePermission):

    message = "Faqat bot servisiga ruxsat."

    def has_permission(self, request, view):
        expected = getattr(settings, "BOT_API_TOKEN", "")
        if not expected:
            return False
        token = request.headers.get("X-Bot-Token", "")
        return token == expected