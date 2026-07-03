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
    list_display = ("key", "graph", "node_type", "label")
    list_filter = ("graph", "node_type__category")
    search_fields = ("key", "label", "graph__slug")
    autocomplete_fields = ("node_type", "graph", "group")


@admin.register(NodeGroup)
class NodeGroupAdmin(admin.ModelAdmin):
    list_display = ("key", "graph", "name", "collapsed")
    search_fields = ("key", "name")


@admin.register(Gateway)
class GatewayAdmin(admin.ModelAdmin):
    list_display = ("slug", "graph", "node", "boundary")
    search_fields = ("slug", "name")
