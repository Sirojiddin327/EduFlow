from django.urls import path

from apps.bot_api.views import BotLinkView, BotWhoamiView

urlpatterns = [
    path("link/", BotLinkView.as_view(), name="bot-link"),
    path("whoami/", BotWhoamiView.as_view(), name="bot-whoami"),
]