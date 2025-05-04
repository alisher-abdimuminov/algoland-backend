import time
import json
import redis
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from utils.secrets import encode, decode, jsonify
from users.models import User

from .functions import (
    save_user_last_seen,
    read_notifications,
    run_sandbox,
    like_post,
    follow,
    unfollow,
)


redis_client = redis.Redis(db=1, decode_responses=True)


class AlgoLandConsumer(AsyncWebsocketConsumer):
    # handle connection connect
    async def connect(self):
        self.user: User = self.scope.get("user")

        # groups
        self.main_group = "main"
        self.user_group = f"user_{self.user.pk}"

        # accept connection
        await self.accept()

        # add groups to channel
        await self.channel_layer.group_add(self.main_group, self.channel_name)
        await self.channel_layer.group_add(self.user_group, self.channel_name)

        # check user and change user last_seen to main group
        if self.user.is_authenticated:
            redis_client.incr(f"user_connections_{self.user.pk}")
            redis_client.expire(f"user_connections_{self.user.pk}", 60)
            await sync_to_async(save_user_last_seen)(self.user, "online")
            await self.channel_layer.group_send(
                self.main_group,
                {
                    "type": "last_seen",
                    "data": {
                        "uuid": self.user.uuid.__str__(),
                        "last_seen": "online",
                    },
                }
            )
        print(self.user)

    # handle connection disconnect
    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            remaining = redis_client.decr(f"user_connections_{self.user.pk}")

            if remaining <= 0:
                await sync_to_async(save_user_last_seen)(self.user, f"{int(time.time())}")
                await self.channel_layer.group_send(
                    self.main_group,
                    {
                        "type": f"last_seen",
                        "data": {
                            "uuid": self.user.uuid.__str__(),
                            "last_seen": f"{int(time.time())}",
                        },
                    }
                )

        # discard groups to channel
        await self.channel_layer.group_discard(self.main_group, self.channel_name)
        await self.channel_layer.group_discard(self.user_group, self.channel_name)

    # handle connections receive
    async def receive(self, text_data: str):
        data = jsonify(decode(text_data))
        print(data)

        type = data.get("type")

        # receive read_notification action from client
        if type == "read_notifications":
            if self.user.is_authenticated:
                await sync_to_async(read_notifications)(self.user)

        # receive attempt action from client
        elif type == "attempt":
            if self.user.is_authenticated:
                await sync_to_async(run_sandbox)(self.user, data.get("data", {}).get("problem"), data.get("data", {}).get("language"), data.get("data", {}).get("code"))

        elif type == "like_to_post":
            if self.user.is_authenticated:
                await sync_to_async(like_post)(self.user, data.get("data", {}).get("uuid"))

        elif type == "follow":
            if self.user.is_authenticated:
                await sync_to_async(follow)(self.user, data.get("data", {}).get("username"))
        
        elif type == "unfollow":
            if self.user.is_authenticated:
                await sync_to_async(unfollow)(self.user, data.get("data", {}).get("username"))


    # send notification event
    async def notification(self, event: dict):
        print(event)
        await self.send(text_data=encode(json.dumps({
            "type": "notification",
            **event
        })))

    # send user last seen event
    async def last_seen(self, event: dict):
        print(event)
        await self.send(text_data=encode(json.dumps({
            "type": "last_seen",
            **event,
        })))

    # send attempt case
    async def attempt_case(self, event: dict):
        await self.send(text_data=encode(json.dumps({
            "type": "attempt_case",
            **event,
        })))
    
    async def attempt_status(self, event: dict):
        await self.send(text_data=encode(json.dumps({
            "type": "attempt_status",
            **event,
        })))

    async def update_post(self, event: dict):
        await self.send(text_data=encode(json.dumps({
            "type": "update_post",
            **event,
        })))
