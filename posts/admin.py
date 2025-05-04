from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    Post,
    Tag,
    Comment,
)


@admin.register(Post)
class PostModelAdmin(ModelAdmin):
    list_display = ["title", "description", ]


@admin.register(Tag)
class TagModelAdmin(ModelAdmin):
    list_display = ["name"]

