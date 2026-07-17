import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import StudySession

class TimerConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.session_group_name = f'session_{self.session_id}'

        await self.channel_layer.group_add(
            self.session_group_name,
            self.channel_name
        )

        await self.accept()

        # Send the current timer state to the newly connected client
        session = await self.get_session()
        if session and session.is_active:
            await self.send(text_data=json.dumps({
                'type': 'timer_update',
                'remaining_seconds': session.remaining_seconds
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.session_group_name,
            self.channel_name
        )

    async def timer_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'timer_update',
            'remaining_seconds': event['remaining_seconds']
        }))

    @database_sync_to_async
    def get_session(self):
        try:
            return StudySession.objects.get(id=self.session_id)
        except StudySession.DoesNotExist:
            return None