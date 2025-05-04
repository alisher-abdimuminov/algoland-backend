from django.urls import path

from .views import (
    PostsListAPIView,
    get_post,
    add_post,
    edit_post,
    get_tags,
)


urlpatterns = [
    path("posts/", PostsListAPIView.as_view(),),
    path("posts/post/<str:uuid>/", get_post,),
    path("posts/post/<str:uuid>/edit/", edit_post,),
    path("posts/add/", add_post, ),

    path("posts/tags/", get_tags,),
]
