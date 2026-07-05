from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import GraphBakeView, IccChartView, ReleaseIccChartView, ReleaseViewSet

router = DefaultRouter()
router.register(r"releases", ReleaseViewSet, basename="release")

urlpatterns = router.urls + [
    path("graphs/<int:pk>/bake/", GraphBakeView.as_view(), name="graph-bake"),
    path("graphs/<int:pk>/icc-chart/", IccChartView.as_view(), name="graph-icc-chart"),
    path("releases/<int:pk>/icc-chart/", ReleaseIccChartView.as_view(), name="release-icc-chart"),
]
