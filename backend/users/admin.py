from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Follow

User = get_user_model()


if admin.site.is_registered(User):
    admin.site.unregister(User)


class UserAdmin(BaseUserAdmin):
    list_display = (
        'email',
        'first_name',
        'last_name'
    )
    list_filter = (
        'username',
        'email'
    )


admin.site.register(User, UserAdmin)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'author'
    )
    empty_value_display = 'Нет записей'
