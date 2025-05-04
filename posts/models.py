from uuid import uuid4
from django.db import models

from users.models import User


class Tag(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Post(models.Model):
    uuid = models.CharField(max_length=100, default=uuid4)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000)
    image = models.CharField(max_length=100, null=True, blank=True)
    description = models.CharField(max_length=200)
    content = models.TextField()
    tags = models.ManyToManyField(Tag, related_name="post_tags", blank=True)
    viewers = models.ManyToManyField(User, related_name="post_viewers", blank=True)
    likes = models.ManyToManyField(User, related_name="post_likes", blank=True)
    dislikes = models.ManyToManyField(User, related_name="post_dislikes", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    

class Comment(models.Model):
    uuid = models.UUIDField(default=uuid4, editable=False, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post_comment_author")
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    reply = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    content = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.post.title
