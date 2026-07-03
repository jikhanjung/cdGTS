from django.contrib import admin

from .models import (
    BoundaryRecord, CandidateOutput, Clamp, ModelCandidate, Release, Selection,
)


class CandidateOutputInline(admin.TabularInline):
    model = CandidateOutput
    extra = 0
    autocomplete_fields = ("boundary",)


@admin.register(ModelCandidate)
class ModelCandidateAdmin(admin.ModelAdmin):
    list_display = ("slug", "scope", "kind", "method")
    list_filter = ("scope", "method")
    search_fields = ("slug", "kind")
    inlines = (CandidateOutputInline,)


class SelectionInline(admin.TabularInline):
    model = Selection
    extra = 0
    autocomplete_fields = ("boundary", "candidate")


class BoundaryRecordInline(admin.TabularInline):
    model = BoundaryRecord
    extra = 0
    autocomplete_fields = ("boundary", "candidate")
    readonly_fields = ("boundary", "definition_type", "value_ma", "method")
    can_delete = False


@admin.register(Release)
class ReleaseAdmin(admin.ModelAdmin):
    list_display = ("version", "authority", "created_at")
    search_fields = ("version",)
    filter_horizontal = ("clamps",)
    inlines = (SelectionInline, BoundaryRecordInline)


@admin.register(Clamp)
class ClampAdmin(admin.ModelAdmin):
    list_display = ("slug", "kind", "owner", "target_boundary", "overridable_in_sandbox")
    list_filter = ("kind",)
    search_fields = ("slug",)


@admin.register(BoundaryRecord)
class BoundaryRecordAdmin(admin.ModelAdmin):
    list_display = ("release", "boundary", "definition_type", "value_ma", "method")
    list_filter = ("release", "definition_type", "method")
    search_fields = ("boundary__slug",)
