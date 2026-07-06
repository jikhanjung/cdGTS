from django.contrib import admin

from .models import Edge, Gateway, Graph, NodeGroup, NodeInstance


class NodeInstanceInline(admin.TabularInline):
    model = NodeInstance
    extra = 0
    autocomplete_fields = ("node_type",)


class EdgeInline(admin.TabularInline):
    model = Edge
    extra = 0
    autocomplete_fields = ("source", "target")


class GatewayInline(admin.TabularInline):
    model = Gateway
    extra = 0
    autocomplete_fields = ("node", "boundary")


@admin.register(Graph)
class GraphAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "status", "owner", "updated_at")
    list_filter = ("status",)
    search_fields = ("slug", "name")
    prepopulated_fields = {"slug": ("name",)}
    inlines = (NodeInstanceInline, EdgeInline, GatewayInline)


@admin.register(NodeInstance)
class NodeInstanceAdmin(admin.ModelAdmin):
    list_display = ("key", "graph", "node_type", "nature", "label")
    list_filter = ("graph", "nature", "node_type__category")
    search_fields = ("key", "label", "graph__slug")
    autocomplete_fields = ("node_type", "graph", "group")


@admin.register(NodeGroup)
class NodeGroupAdmin(admin.ModelAdmin):
    list_display = ("key", "graph", "name", "kind", "unit", "collapsed")
    list_filter = ("kind",)
    search_fields = ("key", "name")
    autocomplete_fields = ("unit", "lower", "upper", "parent")


@admin.register(Gateway)
class GatewayAdmin(admin.ModelAdmin):
    list_display = ("slug", "graph", "node", "boundary")
    search_fields = ("slug", "name")
