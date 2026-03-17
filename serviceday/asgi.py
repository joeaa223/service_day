import os

print("ASGI FILE LOADED")

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

import serviceday.routing

print("ROUTING IMPORTED", serviceday.routing.websocket_urlpatterns)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "serviceday.settings")

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(serviceday.routing.websocket_urlpatterns)
    ),
})