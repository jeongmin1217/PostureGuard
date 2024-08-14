from channels.generic.websocket import AsyncWebsocketConsumer
import json

class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("logs_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("logs_group", self.channel_name)

    async def receive(self, text_data):
        # 수신된 메시지 처리 (필요에 따라 구현)
        pass

    async def logs_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps(message))
