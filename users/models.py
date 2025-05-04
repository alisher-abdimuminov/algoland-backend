from uuid import uuid4
from django.db import models
from django.contrib.auth.models import AbstractUser

from .manager import UserManager



GENDER = (
    ("male", "Erkak"),
    ("female", "Ayol"),
)

ROLE = (
    ("admin", "Admin"),
    ("user", "User"),
)

NOTIFICATION_TYPE = (
    ("admin", "Admin"),
    ("follow", "Follow"),
    ("unfollow", "Unfollow"),
    ("like", "Like"),
    ("comment", "Comment"),
    ("post", "New post"),
)


class User(AbstractUser):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    
    gender = models.CharField(max_length=8, choices=GENDER)
    
    country = models.CharField(null=True, blank=True)
    city = models.CharField(max_length=32, null=True, blank=True)
    
    image = models.CharField(max_length=1024, null=True, blank=True)
    bio = models.CharField(max_length=128, null=True, blank=True)
    
    rating = models.IntegerField(default=1500)
    last_seen = models.CharField(max_length=16, default="offline")
    
    role = models.CharField(max_length=8, choices=ROLE)
    permissions = models.JSONField(default=list, null=True, blank=True)

    is_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    premium_expires = models.DateTimeField(null=True, blank=True)

    coach = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True)
    followers = models.ManyToManyField("self", symmetrical=False, related_name="user_followers", blank=True)
    following = models.ManyToManyField("self", symmetrical=False, related_name="user_following", blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "username"

    def __str__(self):
        return self.username


class Session(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)

    author = models.ForeignKey(User, on_delete=models.CASCADE)

    device = models.JSONField(default=dict)
    browser = models.JSONField(default=dict)
    os = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField()
    is_active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.device
    

class Activity(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    attempts = models.IntegerField(default=0)
    problems = models.IntegerField(default=0)
    activity = models.IntegerField(default=0)
    
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.uuid.__str__()
    

class Notification(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)

    type = models.CharField(max_length=32, choices=NOTIFICATION_TYPE)
    to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    params = models.JSONField(default=dict, null=True, blank=True)
    is_readed = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.type



