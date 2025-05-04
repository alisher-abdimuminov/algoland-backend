from django.contrib import admin
from unfold.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import User


@admin.register(User)
class UserModelAdmin(UserAdmin, ModelAdmin):
    list_display = [
        "username",
        "first_name",
        "last_name",
        "email",
        "is_active",
        "is_verified",
        "is_premium",
        "last_seen",
    ]

    model = User
    form = UserChangeForm
    add_form = UserCreationForm

    add_fieldsets = (
        (
            "Ma'lumotlar",
            {
                "fields": (
                    "username",
                    "password1",
                    "password2",
                    "email",
                    "first_name",
                    "last_name",
                    "gender",
                    "role",
                )
            },
        ),
    )

    fieldsets = (
        (
            "Ma'lumotlar",
            {
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "gender",
                ),
            },
        ),
        (
            "Joylashuv",
            {
                "fields": ("country", "city"),
            },
        ),
        (
            "Qo'shimcha",
            {
                "fields": (
                    "role",
                    "image",
                    "bio",
                    "premium_expires",
                )
            },
        ),
        (
            "Is",
            {
                "fields": (
                    "is_active",
                    "is_verified",
                    "is_premium",
                )
            },
        ),
    )
