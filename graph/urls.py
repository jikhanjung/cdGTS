from rest_framework.routers import DefaultRouter

from .views import GraphViewSet

router = DefaultRouter()
router.register(r"graphs", GraphViewSet, basename="graph")

urlpatterns = router.urls
