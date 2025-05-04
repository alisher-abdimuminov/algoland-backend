import json
from django.http import HttpRequest
from rest_framework.response import Response
from rest_framework import decorators
from rest_framework import permissions
from rest_framework import authentication
from rest_framework import generics
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend

from utils.secrets import encode, decode, jsonify
from users.models import User

from .models import (
    Post,
    Tag,
)
from .serializers import (
    PostsModelSerializer,
    PostModelSerializer,
    PostTagModelSerializer,
    EditPostModelSerializer,
)
from .pagination import (
    PostsPagination,
)


class PostsListAPIView(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostsModelSerializer
    pagination_class = PostsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,]
    # filterset_fields = ["difficulty", ]
    permission_classes = [permissions.AllowAny,]
    search_fields = ["title", "description", "content", ]


@decorators.api_view(http_method_names=["GET"])
def get_tags(request: HttpRequest):
    tags = Tag.objects.all()
    tags_serializer = PostTagModelSerializer(tags, many=True)
    return Response({
        "status": "success",
        "code": "get_tags_001",
        "data": encode(json.dumps(tags_serializer.data))
    })


@decorators.api_view(http_method_names=["GET"])
def get_post(request: HttpRequest, uuid: str):
    post = Post.objects.filter(uuid=uuid)

    if not post.exists():
        return Response({
            "status": "error",
            "code": "get_post_001",
            "data": None
        })
    
    post = post.first()

    user = request.user

    if user.is_authenticated:
        if not post.viewers.contains(user):
            post.viewers.add(user)

    post_serializer = PostModelSerializer(post, context={ "request": request })

    return Response({
        "status": "success",
        "code": "get_problem_002",
        "data": encode(json.dumps(post_serializer.data))
    })


@decorators.api_view(http_method_names=["POST"])
@decorators.permission_classes(permission_classes=[permissions.IsAuthenticated])
@decorators.authentication_classes(authentication_classes=[authentication.TokenAuthentication])
def add_post(request: HttpRequest):
    user: User = request.user
    post = Post.objects.create(
        author=user,
        title="This is post title",
        description="This is post description",
        content="This is post content",
    )
    return Response({
        "status": "success",
        "code": "add_post_001",
        "data": encode(json.dumps({
            "uuid": str(post.uuid)
        }))
    })


@decorators.api_view(http_method_names=["POST"])
@decorators.permission_classes(permission_classes=[permissions.IsAuthenticated])
@decorators.authentication_classes(authentication_classes=[authentication.TokenAuthentication])
def edit_post(reuqest: HttpRequest, uuid: str):
    post = Post.objects.filter(uuid=uuid)
    decoded = jsonify(decode(reuqest.data.get("data", "")))

    if not post.exists():
        return Response({
            "status": "error",
            "code": "edit_post_001", # post not found
            "data": None
        })
    
    post = post.first()

    post_serializer = EditPostModelSerializer(post, data=dict(filter(lambda x: x[1] is not None, decoded.items())), partial=True)

    if post_serializer.is_valid():
        post = post_serializer.save()
        return Response({
            "status": "success",
            "code": "edit_problem_002",
            "data": encode(json.dumps(PostModelSerializer(post, context={ "request": reuqest }).data)),
        })
    
    errors = post_serializer.errors

    return Response({
        "status": "error",
        "code": "edit_problem_003",
        "data": encode(json.dumps([key for key in dict(errors).keys()])),
    })
