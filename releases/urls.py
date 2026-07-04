from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import GraphBakeView, ReleaseViewSet

router = DefaultRouter()
router.register(r"releases", ReleaseViewSet, basename="release")

urlpatterns = router.urls + [
    path("graphs/<int:pk>/bake/", GraphBakeView.as_view(), name="graph-bake"),
]
