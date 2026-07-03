from django.contrib import admin

from .models import CoherenceCertificate, EvalRun, NodeResult


class NodeResultInline(admin.TabularInline):
    model = NodeResult
    extra = 0
    readonly_fields = ("node_key", "content_hash", "distribution", "provenance", "cached")
    can_delete = False


@admin.register(EvalRun)
class EvalRunAdmin(admin.ModelAdmin):
    list_display = ("id", "graph", "created_at", "stats")
    list_filter = ("graph",)
    inlines = (NodeResultInline,)


@admin.register(CoherenceCertificate)
class CoherenceCertificateAdmin(admin.ModelAdmin):
    list_display = ("eval_run", "passed", "checks")
