from django.urls import path

from .views import (
    ProblemAttemptsListAPIView,
    ProblemsListAPIView,
    get_languages,
    get_tags,
    get_problem,
    edit_problem,
    add_problem,
)


urlpatterns = [
    path("problems/", ProblemsListAPIView.as_view(), ),
    path("problems/problem/<str:uuid>/", get_problem, ),
    path("problems/problem/<str:uuid>/edit/", edit_problem, ),
    path("problems/problem/<str:uuid>/attempts/", ProblemAttemptsListAPIView.as_view(), ),
    path("problems/add/", add_problem, ),

    path("languages/", get_languages),
    path("problems/tags/", get_tags,),
]
