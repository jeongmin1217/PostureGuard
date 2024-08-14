"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.conf.urls import url
from channels.staticfiles import StaticFilesWrapper
from logs.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # HTTP 및 정적 파일 요청 처리
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns  # WebSocket 경로
        )
    ),
})
