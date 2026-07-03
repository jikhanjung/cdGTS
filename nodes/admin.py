from django.contrib import admin

from .models import NodeType, Port


class PortInline(admin.TabularInline):
    model = Port
    extra = 0
    ordering = ("direction", "order")


@admin.register(NodeType)
class NodeTypeAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "category", "port_summary")
    list_filter = ("category",)
    search_fields = ("slug", "name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (PortInline,)

    @admin.display(description="ports (in → out)")
    def port_summary(self, obj):
        ins = ", ".join(p.name for p in obj.input_ports) or "—"
        outs = ", ".join(p.name for p in obj.output_ports) or "—"
        return f"{ins} → {outs}"


@admin.register(Port)
class PortAdmin(admin.ModelAdmin):
    list_display = ("node_type", "name", "direction", "datatype", "multiple")
    list_filter = ("direction", "datatype", "node_type__category")
    search_fields = ("name", "node_type__slug")
