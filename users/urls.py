from django.urls import path

from .views import (
    login,
    signup,
    logout,
    profile,
    get_user,
    verify_email,
    get_sessions,
    edit_profile,
    get_activities,
    disable_session,
    get_notifications,
    get_translations,
    UsersListAPIView,
)


urlpatterns = [
    path("auth/login/", login,),
    path("auth/signup/", signup,),
    path("auth/logout/", logout),
    path("auth/verify/<str:token>/", verify_email),
    path("auth/profile/", profile),
    path("auth/profile/edit/", edit_profile),
    path("auth/sessions/", get_sessions),
    path("auth/sessions/<str:session_key>/disable/", disable_session),

    path("users/", UsersListAPIView.as_view(),),
    path("users/<str:username>/", get_user),
    path("users/<str:username>/activities/", get_activities),
    path("translations/", get_translations,),
    path("notifications/", get_notifications,),
]
