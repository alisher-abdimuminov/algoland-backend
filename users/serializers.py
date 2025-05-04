from rest_framework import serializers

from .models import (
    Notification,
    Session,
    User,
)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "uuid",
            "username",
            "first_name",
            "last_name",
            "country",
            "image",
            "is_premium",
            "rating",
            "last_seen",
        )


class UserSerializer(serializers.ModelSerializer):
    coach = ProfileSerializer()
    followers = serializers.SerializerMethodField("count_followers")
    following = serializers.SerializerMethodField("count_following")

    def count_followers(self, obj: User):
        return obj.followers.count()

    def count_following(self, obj: User):
        return obj.following.count()

    class Meta:
        model = User
        fields = (
            "uuid",
            "username",
            "first_name",
            "last_name",
            "email",
            "gender",
            "country",
            "city",
            "image",
            "bio",
            "rating",
            "last_seen",
            "role",
            "permissions",
            "is_premium",
            "coach",
            "followers",
            "following",
            "created",
        )


class UserEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "gender", "country", "city", "bio",)

    
class SessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Session
        fields = ("uuid", "device", "os", "browser", "ip_address", "is_active", )


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ("uuid", "to", "type", "params", "is_readed", "created",)
