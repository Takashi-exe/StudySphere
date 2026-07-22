import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from redis.exceptions import RedisError
from .models import Message, Conversation
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        try:
            await self.channel_layer.group_add(
                self.conversation_group_name,
                self.channel_name
            )
        except RedisError:
            # Can't join the fan-out group if Redis is unreachable; close this
            # socket cleanly rather than accepting a connection that can never
            # send or receive.
            logger.exception("Redis error on group_add for %s", self.conversation_group_name)
            await self.close(code=1011)
            return

        await self.accept()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
        except RedisError:
            # Best-effort cleanup; the group membership expires on its own.
            logger.warning("Redis error on group_discard for %s", self.conversation_group_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']

        if not message:
            return

        new_message = await self.save_message(message)

        try:
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'chat_message',
                    'message': new_message.text,
                    'sender': self.user.username
                }
            )
        except RedisError:
            # A transient Redis timeout must not crash this consumer (which would
            # drop the user's whole connection). Log and notify only this client.
            logger.exception("Redis error on group_send for %s", self.conversation_group_name)
            await self.send(text_data=json.dumps({
                'error': 'Message could not be delivered right now. Please try again.'
            }))

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender']
        }))

    @database_sync_to_async
    def save_message(self, message):
        conversation = Conversation.objects.get(id=self.conversation_id)
        return Message.objects.create(conversation=conversation, sender=self.user, text=message)