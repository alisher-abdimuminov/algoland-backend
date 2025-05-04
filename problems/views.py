import json
import time
from django.http import HttpRequest
from rest_framework import filters
from rest_framework import generics
from rest_framework import decorators
from rest_framework import permissions
from rest_framework import authentication
from django.db.models import Window, F, Q
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from django.db.models.functions import RowNumber
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django_filters.rest_framework import DjangoFilterBackend

from utils.secrets import encode, decode, jsonify
from users.models import User

from .models import (
    Problem,
    Language,
    Attempt,
    Tag,
)
from .serializers import (
    ProblemsModelSerializer,
    ProblemModelSerializer,
    LanguageModelSerializer,
    EditProblemSerializer,
    AttemptsModelSerializer,
    TagModelSerializer,
)
from .pagination import (
    AttemptsPagination,
    ProblemsPagination,
)


@decorators.api_view(http_method_names=["GET"])
def get_languages(request: HttpRequest):
    languages = Language.objects.all()
    languages_serializer = LanguageModelSerializer(languages, many=True)
    return Response({
        "status": "success",
        "code": "get_languages_001",
        "data": encode(json.dumps(languages_serializer.data))
    })


@decorators.api_view(http_method_names=["GET"])
def get_tags(request: HttpRequest):
    tags = Tag.objects.all()
    tags_serializer = TagModelSerializer(tags, many=True)
    return Response({
        "status": "success",
        "code": "get_tags_001",
        "data": encode(json.dumps(tags_serializer.data))
    })


class ProblemAttemptsListAPIView(generics.ListAPIView):
    serializer_class = AttemptsModelSerializer
    pagination_class = AttemptsPagination
    permission_classes = [permissions.IsAuthenticated,]
    authentication_classes = [authentication.TokenAuthentication,]

    def get_queryset(self):
        user: User = self.request.user
        problem_uuid = self.kwargs.get("uuid")
        problem = Problem.objects.filter(uuid=problem_uuid)
        if not problem.exists():
            return []
        problem = problem.first()
        attempts = Attempt.objects.filter(author=user, problem=problem).order_by("-id")
        return attempts


class ProblemsListAPIView(generics.ListAPIView):
    serializer_class = ProblemsModelSerializer
    pagination_class = ProblemsPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,]
    filterset_fields = ["difficulty", ]
    permission_classes = [permissions.AllowAny,]
    search_fields = ["title", "description", ]

    def get_queryset(self):
        user: User = self.request.user

        queryset = Problem.objects.annotate(
            order=Window(
                expression=RowNumber(),
                order_by=F("id").asc()
            )
        )
        
        if user.is_authenticated:
            if user.role == "admin":
                return queryset
            return queryset.filter(
                Q(is_public=True) | Q(author=user)
            )
        return queryset.filter(is_public=True)


@decorators.api_view(http_method_names=["GET"])
def get_problem(request: HttpRequest, uuid: str):
    user = request.user
    problem = Problem.objects.annotate(
        order=Window(
        expression=RowNumber(),
            order_by=F("id").asc()
        )
    ).filter(uuid=uuid)

    if not problem:
        return Response({
            "status": "error",
            "code": "get_problem_001",
            "data": None
        })
    
    problem = problem.first()

    if not problem.is_public:
        if not problem.with_link:
            if not user.is_authenticated:
                return Response({
                    "status": "error",
                    "code": "get_problem_002", # problem is private
                    "data": None
                })
            elif user.pk != problem.author.pk:
                return Response({
                    "status": "error",
                    "code": "get_problem_003", # problem is private
                    "data": None
                })
        
    problem_serializer = ProblemModelSerializer(problem, context={ "request": request })

    return Response({
        "status": "success",
        "code": "get_problem_004",
        "data": encode(json.dumps(problem_serializer.data))
    })


@decorators.api_view(http_method_names=["POST"])
@decorators.authentication_classes(authentication_classes=[authentication.TokenAuthentication])
@decorators.permission_classes(permission_classes=[permissions.IsAuthenticated])
def edit_problem(request: HttpRequest, uuid: str):
    user = request.user
    decoded = jsonify(decode(request.data.get("data", "")))
    print(decoded)
    problem = Problem.objects.filter(uuid=uuid)

    if not problem.exists():
        return Response({
            "status": "error",
            "code": "edit_problem_001", # problem not found
            "data": None
        })
    
    problem = problem.first()

    if problem.author.pk != user.pk:
        return Response({
            "status": "error",
            "code": "edit_problem_002",
            "data": None
        })

    problem_serializer = EditProblemSerializer(problem, data=dict(filter(lambda x: x[1] is not None, decoded.items())), partial=True)

    if problem_serializer.is_valid():
        problem_serializer.save()
        return Response({
            "status": "success",
            "code": "edit_problem_003",
            "data": None
        })
    
    print(problem_serializer.errors)

    return Response({
        "status": "error",
        "code": "edit_problem_004",
        "data": None
    })


@decorators.api_view(http_method_names=["POST"])
@decorators.authentication_classes(authentication_classes=[authentication.TokenAuthentication])
@decorators.permission_classes(permission_classes=[permissions.IsAuthenticated])
def add_problem(request: HttpRequest):
    user: User = request.user

    time.sleep(5)
    print("method", request.method)
    problem = Problem.objects.create(
        title="Problem title",
        language="uz",
        author=user,
    )
    return Response({
        "status": "success",
        "code": "add_problem_001",
        "data": encode(json.dumps({
            "uuid": problem.uuid.__str__()
        }))
    })

