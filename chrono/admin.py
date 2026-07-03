from django.contrib import admin

from .models import Authority, Boundary, BoundaryLineage, Locality, Ratification, Unit


class RatificationInline(admin.TabularInline):
    model = Ratification
    extra = 0


class LocalityInline(admin.StackedInline):
    model = Locality
    extra = 0


class BoundaryLineageInline(admin.TabularInline):
    model = BoundaryLineage
    fk_name = "boundary"
    extra = 0
    filter_horizontal = ("sources",)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "get_rank_display", "chronostratigraphic_term", "geochronologic_term", "parent")
    list_filter = ("rank",)
    search_fields = ("name", "slug")
    autocomplete_fields = ("parent",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Authority)
class AuthorityAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "parent")
    list_filter = ("kind",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Boundary)
class BoundaryAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "definition_type", "below", "above")
    list_filter = ("definition_type",)
    search_fields = ("slug", "name")
    autocomplete_fields = ("below", "above")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (LocalityInline, RatificationInline, BoundaryLineageInline)


@admin.register(Locality)
class LocalityAdmin(admin.ModelAdmin):
    list_display = ("name", "boundary", "level", "latitude", "longitude")
    search_fields = ("name", "boundary__slug")


@admin.register(Ratification)
class RatificationAdmin(admin.ModelAdmin):
    list_display = ("boundary", "year", "authority")
    list_filter = ("authority", "year")
