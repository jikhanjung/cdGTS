from rest_framework.routers import DefaultRouter

from .views import ReferenceViewSet

router = DefaultRouter()
router.register(r"references", ReferenceViewSet, basename="reference")

urlpatterns = router.urls
