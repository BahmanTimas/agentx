from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .views import landing, app_start, chat_start, on_message, oauth_callback


urlpatterns = [
    path("", csrf_exempt(landing), name = "landing"),
    path("app-start", csrf_exempt(app_start), name = "app-start"),
    path('chat-start', csrf_exempt(chat_start)),
    path('hook/on-message', csrf_exempt(on_message)),
    path('auth/divar/callback', csrf_exempt(oauth_callback)),
]
