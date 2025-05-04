from datetime import datetime
import json
from user_agents import parse
from django.http import HttpRequest
from rest_framework import decorators
from rest_framework import permissions
from rest_framework import generics
from rest_framework import filters
from django.db import connection
from rest_framework import authentication
from django.core.paginator import Paginator
from rest_framework.response import Response
from django.db.models import Q
from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework.authtoken.models import Token

from utils.mail import send
from utils.worker import Worker
from utils.secrets import encode, decode, jsonify
from utils.functions import check_email, check_username

from config.settings import REST_FRAMEWORK

from .models import Notification, User, Session
from .serializers import (
    NotificationSerializer,
    SessionSerializer,
    UserSerializer,
    UserEditSerializer,
    ProfileSerializer,
)


@decorators.api_view(["GET"])
def get_translations(request: HttpRequest):
    try:
        with open("translations.json", "r") as t:
            translations = json.load(t)
            return Response(
                {
                    "status": "success",
                    "code": "get_translations_001",
                    "data": encode(json.dumps(translations)),
                }
            )
    except Exception as e:
        print(e)
        return Response(
            {
                "status": "error",
                "code": "get_translations_002",
                "data": None,
            }
        )


@decorators.api_view(http_method_names=["POST"])
def login(request: HttpRequest):
    ua = parse(request.headers.get("User-Agent"))
    decoded = jsonify(decode(request.data.get("data", "")))

    username = decoded.get("username")
    password = decoded.get("password")

    if not username:
        return Response(
            {
                "status": "error",
                "code": "login_001",  # username is required
                "data": None,
            }
        )

    if not password:
        return Response(
            {
                "status": "error",
                "code": "login_002",  # password is required
                "data": None,
            }
        )

    user = User.objects.filter(username=username)

    if not user.exists():
        return Response(
            {
                "status": "error",
                "code": "login_003",  # user not found
                "data": None,
            }
        )

    user = user.first()

    if not user.check_password(raw_password=password):
        return Response(
            {
                "status": "error",
                "code": "login_004",  # password didnot match
                "data": None,
            }
        )

    if not user.is_active:
        return Response(
            {
                "status": "error",
                "code": "login_005",  # user is not active
                "data": None,
            }
        )

    if not user.is_verified:
        return Response(
            {
                "status": "error",
                "code": "login_006",  # user is not verified
                "data": None,
            }
        )

    token = Token.objects.get_or_create(user=user)
    session = Session.objects.create(
        author=user,
        device={
            "family": ua.device.family,
            "brand": ua.device.brand,
            "model": ua.device.model,
        },
        os={
            "family": ua.os.family,
            "version": ua.os.version_string,
        },
        browser={
            "family": ua.browser.family,
            "version": ua.browser.version_string,
        },
        ip_address=request.META.get("REMOTE_ADDR"),
    )

    return Response(
        {
            "status": "success",
            "code": "login_007",
            "data": encode(
                json.dumps(
                    {
                        **UserSerializer(user).data,
                        "token": token[0].key,
                        "session": session.uuid.__str__(),
                    }
                )
            ),
        }
    )


@decorators.api_view(http_method_names=["POST"])
def signup(request: HttpRequest):
    decoded = jsonify(decode(request.data.get("data", "")))

    username = decoded.get("username")
    password = decoded.get("password")
    first_name = decoded.get("first_name")
    last_name = decoded.get("last_name")
    email = decoded.get("email")
    gender = decoded.get("gender")
    country = decoded.get("country")

    if not username:
        return Response(
            {
                "status": "error",
                "code": "signup_001",  # usernaem is reuqired
                "data": None,
            }
        )

    if not password:
        return Response(
            {
                "status": "error",
                "code": "signup_002",  # password is required
                "data": None,
            }
        )

    if not first_name:
        return Response(
            {
                "status": "error",
                "code": "signup_003",  # first_name is required
                "data": None,
            }
        )

    if not last_name:
        return Response(
            {
                "status": "error",
                "code": "signup_004",  # last_name is required
                "data": None,
            }
        )

    if not email:
        return Response(
            {
                "status": "error",
                "code": "signup_005",  # email is required
                "data": None,
            }
        )

    if not gender:
        return Response(
            {
                "status": "error",
                "code": "signup_006",  # gender is required
                "data": None,
            }
        )

    if not country:
        return Response(
            {
                "status": "error",
                "code": "signup_007",  # country is required,
                "data": None,
            }
        )

    if gender not in ["male", "female"]:
        return Response(
            {
                "status": "error",
                "code": "signup_008",  # gender is invalid
                "data": None,
            }
        )

    if not check_email(email=email):
        return Response(
            {
                "status": "error",
                "code": "signup_009",  # email is invalid
                "data": None,
            }
        )

    if not check_username(username=username):
        return Response(
            {
                "status": "error",
                "code": "signup_010",  # username is invalid
                "data": None,
            }
        )

    user = User.objects.filter(username=username)

    if user.exists():
        return Response(
            {
                "status": "error",
                "code": "signup_011",  # username already taken
                "data": None,
            }
        )

    user = User.objects.filter(email=email)

    if user.exists():
        return Response(
            {
                "status": "error",
                "code": "signup_012",  # email already used
                "data": None,
            }
        )

    user = User.objects.create(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        country=country,
    )

    user.set_password(raw_password=password)
    user.save()

    encoded = encode(json.dumps({"username": user.username}))

    worker = Worker(
        send,
        user.email,
        "Email verification",
        f"<b>Verify your email</b><br /><a href='https://algoland.uz/auth/verify?token={encoded}' target='_blank'>https://algoland.uz/auth/verify?token={encoded}</a>",
    )
    worker.start()

    return Response(
        {
            "status": "success",
            "code": "signup_013",  # user created
            "data": None,
        }
    )


@decorators.api_view(http_method_names=["POST"])
@decorators.authentication_classes(
    authentication_classes=[authentication.TokenAuthentication]
)
@decorators.permission_classes(permission_classes=[permissions.IsAuthenticated])
def logout(request: HttpRequest):
    decoded = jsonify(decode(request.data.get("data", "")))

    session_key = decoded.get("session")

    if not session_key:
        return Response(
            {
                "status": "error",
                "code": "logout_001",  # session key is required
                "data": None,
            }
        )

    session = Session.objects.filter(uuid=session_key)

    if not session.exists():
        return Response(
            {
                "status": "error",
                "code": "logout_002",  # session is not found
                "data": None,
            }
        )

    session = session.first()

    if not session.is_active:
        return Response(
            {
                "status": "error",
                "code": "logout_003",  # session is already inactive
                "data": None,
            }
        )

    session.is_active = False
    session.save()

    return Response(
        {
            "status": "success",
            "code": "signup_004",  # logout success
            "data": None,
        }
    )


@decorators.api_view(http_method_names=["POST"])
def verify_email(request: HttpRequest, token: str):
    print(decode(token))
    decoded = jsonify(decode(token))

    username = decoded.get("username")

    if not username:
        return Response(
            {
                "status": "error",
                "code": "verify_email_001",  # username is required
                "data": None,
            }
        )

    user = User.objects.filter(username=username)

    if not user.exists():
        return Response(
            {
                "status": "error",
                "code": "verify_email_002",  # user not found
                "data": None,
            }
        )

    user = user.first()

    if user.is_verified:
        return Response(
            {
                "status": "error",
                "code": "verify_email_003",  # user is already verified, token is already used
                "data": None,
            }
        )

    user.is_verified = True
    user.save()

    return Response(
        {
            "status": "success",
            "code": "verify_email_004",  # user verified
            "data": None,
        }
    )


@decorators.api_view(http_method_names=["POST"])
def forget_password(request: HttpRequest):
    decoded = jsonify(decode(request.data.get("data", "")))

    email = decoded.get("email")

    if not email:
        return Response(
            {
                "status": "error",
                "code": "forget_password_001",  # email is required
                "data": None,
            }
        )

    user = User.objects.filter(email=email)

    if not user.exists():
        return Response(
            {
                "status": "error",
                "code": "forget_password_002",  # email not found
                "data": None,
            }
        )

    # send link to email
    return Response(
        {
            "status": "error",
            "code": "forget_password_003",  # link sended to email
            "data": None,
        }
    )


@decorators.api_view(http_method_names=["POST"])
def change_password(request: HttpRequest):
    pass


@decorators.api_view(http_method_names=["GET"])
@decorators.authentication_classes(
    authentication_classes=[authentication.TokenAuthentication]
)
@decorators.permission_classes(permission_classes=[permissions.IsAuthenticated])
def profile(request: HttpRequest):
    decoded = jsonify(decode(request.GET.get("data", "")))

    session_key = decoded.get("session")
    token = decoded.get("token")

    if not session_key:
        return Response(
            {
                "status": "error",
                "code": "profile_001",  # session is required
                "data": None,
            }
        )

    if not token:
        return Response(
            {
                "status": "error",
                "code": "profile_002",  # token is required
                "data": None,
            }
        )

    user: User = request.user

    session = Session.objects.filter(uuid=session_key)

    if not session.exists():
        return Response(
            {
                "status": "error",
                "code": "profile_003",  # session not found
                "data": None,
            }
        )

    session = session.first()

    if not session.is_active:
        return Response(
            {
                "status": "error",
                "code": "get_profile_004",  # session is not active
                "data": None,
            }
        )

    return Response(
        {
            "status": "success",
            "code": "profile_005",
            "data": encode(
                json.dumps(
                    {
                        **UserSerializer(user).data,
                        "token": token,
                        "session": session_key,
                    }
                )
            ),
        }
    )


@decorators.api_view(http_method_names=["POST"])
@decorators.authentication_classes(
    authentication_classes=[authentication.TokenAuthentication]
)
@decorators.permission_classes(permission_classes=[permissions.IsAuthenticated])
def edit_profile(request: HttpRequest):
    decoded = jsonify(decode(request.data.get("data", "")))

    user: User = request.user

    token = decoded.pop("token")
    session = decoded.pop("session")

    user_serializer = UserEditSerializer(user, data=decoded)

    if user_serializer.is_valid():
        user_serializer.save()
        user.refresh_from_db()
        return Response(
            {
                "status": "success",
                "code": "edit_profile_001",
                "data": encode(
                    json.dumps(
                        {
                            **UserSerializer(user).data,
                            "token": token,
                            "session": session,
                        }
                    )
                ),
            }
        )
    else:
        errors = user_serializer.errors()
        print(errors)
        return Response({"status": "error", "code": "edit_profile_002", "data": None})


@decorators.api_view(http_method_names=["GET"])
def get_user(request: HttpRequest, username: str):
    if not username:
        return Response(
            {
                "status": "error",
                "code": "get_user_001",  # username is required
                "data": None,
            }
        )

    user: User = User.objects.filter(username=username)

    if not user.exists():
        return Response(
            {
                "status": "error",
                "code": "get_user_002",  # user not found
                "data": None,
            }
        )

    user = user.first()

    return Response(
        {
            "status": "success",
            "code": "get_user_003",  # user found
            "data": encode(
                json.dumps(ProfileSerializer(user, context={"request": request}).data)
            ),
        }
    )


@decorators.api_view(http_method_names=["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
@decorators.authentication_classes([authentication.TokenAuthentication])
def get_sessions(request: HttpRequest):
    page = request.GET.get("page", 1)

    user: User = request.user

    sessions = Session.objects.filter(author=user).order_by("-created")

    paginator = Paginator(sessions, REST_FRAMEWORK.get("PAGE_SIZE", 10))

    page = paginator.get_page(page)
    has_next = page.has_next()
    has_previous = page.has_previous()

    serializer = SessionSerializer(page.object_list, many=True)

    data = {
        "pages": paginator.num_pages,
        "number": page.number,
        "next": page.next_page_number() if has_next else None,
        "previous": page.previous_page_number() if has_previous else None,
    }

    return Response(
        {
            "status": "success",
            "code": "get_sessions_001",
            "data": encode(
                json.dumps(
                    {
                        "page": data,
                        "sessions": serializer.data,
                    }
                )
            ),
        }
    )



@decorators.api_view(http_method_names=["POST"])
@decorators.permission_classes([permissions.IsAuthenticated])
@decorators.authentication_classes([authentication.TokenAuthentication])
def disable_session(request: HttpRequest, session_key: str):
    if not session_key:
        return Response({
            "status": "error",
            "code": "disable_session_001", # session is required
            "data": None
        })
    
    session = Session.objects.filter(uuid=session_key)

    if not session.exists():
        return Response({
            "status": "error",
            "code": "disable_session_002", # session not found
            "data": None
        })
    
    session = session.first()

    session.is_active = False
    session.save()

    return Response({
        "status": "success",
        "code": "disable_session_003", # session disabled
        "data": None
    })


class UsersListAPIView(generics.ListAPIView):
    queryset = User.objects.order_by("id")
    serializer_class = ProfileSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter,]
    filterset_fields = ["country"]
    search_fields = ["username", "first_name",]


@decorators.api_view(http_method_names=["GET"])
def get_activities(request: HttpRequest, username: str):
    user: User = User.objects.get(username=username)
    start = request.GET.get("start")
    end = request.GET.get("end")

    if start and end:
        with connection.cursor() as cursor:
            cursor.execute("""
                WITH days AS (
                    SELECT generate_series(
                        %s::date,
                        %s::date,
                        INTERVAL '1 day'
                    )::date AS date
                ),
                activity_sum AS (
                    SELECT 
                        DATE(created) AS date,
                        SUM(attempts) AS attempts,
                        SUM(activity) AS activity
                    FROM users_activity
                    WHERE author_id = %s AND created BETWEEN %s::date AND %s::date
                    GROUP BY DATE(created)
                    HAVING SUM(attempts) > 0
                )
                SELECT 
                    d.date,
                    COALESCE(a.attempts, 0) AS attempts,
                    COALESCE(a.activity, 0) AS activity
                FROM days d
                LEFT JOIN activity_sum a ON d.date = a.date
                ORDER BY d.date;
            """, [start, end, user.id, start, end])
            rows = cursor.fetchall()
    else:

        with connection.cursor() as cursor:
            cursor.execute("""
                WITH days AS (
                    SELECT generate_series(
                        CURRENT_DATE - INTERVAL '364 days',
                        CURRENT_DATE,
                        INTERVAL '1 day'
                    )::date AS date
                ),
                activity_sum AS (
                    SELECT 
                        DATE(created) AS date,
                        SUM(attempts) AS attempts,
                        SUM(activity) AS activity
                    FROM users_activity
                    WHERE author_id = %s AND created >= CURRENT_DATE - INTERVAL '364 days'
                    GROUP BY DATE(created)
                )
                SELECT 
                    d.date,
                    COALESCE(a.attempts, 0) AS attempts,
                    COALESCE(a.activity, 0) AS activity
                FROM days d
                LEFT JOIN activity_sum a ON d.date = a.date
                ORDER BY d.date;
            """, [user.id])
            rows = cursor.fetchall()
    return Response({
        "status": "success",
        "code": "get_activities_001",
        "data": encode(json.dumps([{"date": row[0].isoformat(), "attempts": row[1], "activity": row[2]} for row in rows]))
    })


@decorators.api_view(http_method_names=["GET"])
@decorators.permission_classes([permissions.IsAuthenticated])
@decorators.authentication_classes([authentication.TokenAuthentication])
def get_notifications(request: HttpRequest):
    today = datetime.today().date()
    user: User = request.user
    all = request.GET.get("all", False)

    if all:
        notifications = Notification.objects.filter(
            Q(to=user) | Q(type="all")
        ).order_by("-created")
        notifications_serializer = NotificationSerializer(notifications, many=True)
        return Response({
            "status": "success",
            "code": "get_notifications_001",
            "data": encode(json.dumps(notifications_serializer.data))
        })
    
    notifications = Notification.objects.filter(
        (
            Q(is_readed=False) & (Q(to=user) | Q(type="all"))
        ) |
        (
            Q(created__date=today) & (Q(to=user) | Q(type="all"))
        )
    ).order_by("-created")
    notifications_serializer = NotificationSerializer(notifications, many=True)
    return Response({
        "status": "success",
        "code": "get_notifications_002",
        "data": encode(json.dumps(notifications_serializer.data))
    })

