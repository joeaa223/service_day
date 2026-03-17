from django.urls import re_path
from apps.websocket.consumers import WebSocketConsumer

websocket_urlpatterns = [
    re_path(r"websocket/$", WebSocketConsumer.as_asgi()),
]