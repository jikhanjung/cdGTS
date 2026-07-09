from django.contrib import admin

from .models import CoherenceCertificate, EvalJob, EvalRun, NodeResult


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


@admin.register(EvalJob)
class EvalJobAdmin(admin.ModelAdmin):
    list_display = ("id", "graph", "status", "created_at", "started_at", "finished_at", "run")
    list_filter = ("status", "graph")
    readonly_fields = ("created_at", "started_at", "finished_at")
