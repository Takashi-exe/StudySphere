import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import StudyGroup, GroupChatMessage

class GroupChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.group_name = f'group_{self.group_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        if not message:
            return

        new_message = await self.save_message(message)

        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'chat_message',
                'message': new_message.content,
                'user': self.user.username,
                'avatar_url': await self.get_avatar_url(self.user)
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'user': event['user'],
            'avatar_url': event['avatar_url']
        }))

    @database_sync_to_async
    def save_message(self, message):
        group = StudyGroup.objects.get(id=self.group_id)
        return GroupChatMessage.objects.create(group=group, user=self.user, content=message)

    @database_sync_to_async
    def get_avatar_url(self, user):
        if user.profile.avatar:
            return user.profile.avatar.url
        return f"https://ui-avatars.com/api/?name={user.username.replace(' ', '+')}&background=random"

class VoiceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.voice_room = f'group_{self.group_id}_voice'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.voice_room, self.channel_name)
        await self.accept()

        await self.channel_layer.group_send(self.voice_room, {
            'type': 'peer_joined',
            'peer_id': self.user.username,
            'channel_name': self.channel_name,
        })

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(self.voice_room, {
            'type': 'peer_left',
            'peer_id': self.user.username,
        })
        await self.channel_layer.group_discard(self.voice_room, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        if msg_type == 'offer':
            await self.channel_layer.send(data['target'], {
                'type': 'voice_signal',
                'signal_type': 'offer',
                'sdp': data['sdp'],
                'from_peer': self.user.username,
                'from_channel': self.channel_name,
            })

        elif msg_type == 'answer':
            await self.channel_layer.send(data['target'], {
                'type': 'voice_signal',
                'signal_type': 'answer',
                'sdp': data['sdp'],
                'from_peer': self.user.username,
                'from_channel': self.channel_name,
            })

        elif msg_type == 'ice_candidate':
            await self.channel_layer.send(data['target'], {
                'type': 'voice_signal',
                'signal_type': 'ice_candidate',
                'candidate': data['candidate'],
                'from_peer': self.user.username,
                'from_channel': self.channel_name,
            })

    async def peer_joined(self, event):
        await self.send(text_data=json.dumps({
            'type': 'peer_joined',
            'peer_id': event['peer_id'],
            'channel_name': event['channel_name'],
        }))

    async def peer_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'peer_left',
            'peer_id': event['peer_id'],
        }))

    async def voice_signal(self, event):
        await self.send(text_data=json.dumps({
            'type': event['signal_type'],
            'sdp': event.get('sdp'),
            'candidate': event.get('candidate'),
            'from_peer': event['from_peer'],
            'from_channel': event['from_channel'],
        }))