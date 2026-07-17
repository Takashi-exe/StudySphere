# """
# ASGI config for studysphere project.
#
# It exposes the ASGI callable as a module-level variable named ``application``.
#
# For more information on this file, see
# https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
# """
#
# import os
# from channels.auth import AuthMiddlewareStack
# from channels.routing import ProtocolTypeRouter, URLRouter
# from django.core.asgi import get_asgi_application
# import messaging.routing
# import groups.routing
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studysphere.settings')
#
# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             messaging.routing.websocket_urlpatterns +
#             groups.routing.websocket_urlpatterns
#         )
#     ),
# })


import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studysphere.settings')
django.setup()

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import groups.routing
import messaging.routing
import studySessions.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            groups.routing.websocket_urlpatterns +
            messaging.routing.websocket_urlpatterns +
            studySessions.routing.websocket_urlpatterns
        )
    ),
})