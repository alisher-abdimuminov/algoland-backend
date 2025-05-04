from rest_framework import serializers


from users.serializers import ProfileSerializer

from .models import (
    Post,
    Comment,
    Tag,
)


class PostTagModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", )


class PostsModelSerializer(serializers.ModelSerializer):
    author = ProfileSerializer()
    tags = PostTagModelSerializer(many=True)
    viewers = serializers.SerializerMethodField("count_viewers")
    likes = serializers.SerializerMethodField("count_likes")
    comments = serializers.SerializerMethodField("count_comments")
    is_liked = serializers.SerializerMethodField("is_liked_func")

    def count_viewers(self, obj: Post):
        return obj.viewers.count()
    
    def count_likes(self, obj: Post):
        return obj.likes.count()
    
    def count_comments(self, obj: Post):
        return Comment.objects.filter(post=obj).count()
    
    def is_liked_func(self, obj: Post):
        request = self.context.get("request")
        cuser = self.context.get("user")

        if cuser and obj.likes.contains(cuser):
            return True

        if not request:
            return False
        
        user = request.user

        if not user.is_authenticated:
            return False
        
        if obj.likes.contains(user):
            return True
        return False
    
    class Meta:
        model = Post
        fields = ("id", "uuid", "author", "title", "tags", "description", "created", "viewers", "likes", "comments", "is_liked", )


class PostModelSerializer(serializers.ModelSerializer):
    author = ProfileSerializer()
    tags = PostTagModelSerializer(many=True)
    viewers = serializers.SerializerMethodField("count_viewers")
    likes = serializers.SerializerMethodField("count_likes")
    comments = serializers.SerializerMethodField("count_comments")
    is_liked = serializers.SerializerMethodField("is_liked_func")

    def count_viewers(self, obj: Post):
        return obj.viewers.count()
    
    def count_likes(self, obj: Post):
        return obj.likes.count()
    
    def count_comments(self, obj: Post):
        return Comment.objects.filter(post=obj).count()
    
    def is_liked_func(self, obj: Post):
        request = self.context.get("request")
        cuser = self.context.get("user")

        if cuser and obj.likes.contains(cuser):
            return True

        if not request:
            return False
        
        user = request.user

        if not user.is_authenticated:
            return False
        
        if obj.likes.contains(user):
            return True
        return False
    
    class Meta:
        model = Post
        fields = ("id", "uuid", "author", "title", "tags", "image", "content", "description", "created", "likes", "viewers", "comments", "is_liked", )


class EditPostModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("title", "description", "content", "tags", )
