from rest_framework.routers import DefaultRouter

from .views import NodeTypeViewSet

router = DefaultRouter()
router.register(r"node-types", NodeTypeViewSet, basename="nodetype")

urlpatterns = router.urls
