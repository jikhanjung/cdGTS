from django.contrib import admin

from .models import Membership


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "authority", "role", "created_at")
    list_filter = ("role", "authority__kind")
    search_fields = ("user__username", "authority__slug", "authority__name")
    raw_id_fields = ("user", "authority")
