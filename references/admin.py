from django.contrib import admin

from .models import Reference


@admin.register(Reference)
class ReferenceAdmin(admin.ModelAdmin):
    list_display = ("slug", "authors", "year", "doi", "kind")
    list_filter = ("kind", "year")
    search_fields = ("slug", "title", "authors", "doi")
