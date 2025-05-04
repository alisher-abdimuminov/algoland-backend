from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    Attempt,
    Language,
    Problem,
    Tag,
)


@admin.register(Attempt)
class AttemptModelAdmin(ModelAdmin):
    list_display = ["uuid", "author", "problem", "status",]


@admin.register(Language)
class LanguageModelAdmin(ModelAdmin):
    list_display = ["uuid", "name", "short",]


@admin.register(Problem)
class ProblemModelAdmin(ModelAdmin):
    list_display = ["uuid", "title", "author", "is_public"]


@admin.register(Tag)
class TagModelAdmin(ModelAdmin):
    list_display = ["uuid", "name"]
