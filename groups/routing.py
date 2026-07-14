from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/group/(?P<group_id>[0-9a-f-]+)/$', consumers.GroupChatConsumer.as_asgi()),
    re_path(r'ws/voice/(?P<group_id>[0-9a-f-]+)/$', consumers.VoiceConsumer.as_asgi()),
]