from django.urls import path

from .views import EvaluateView

urlpatterns = [
    path("graphs/<int:pk>/evaluate/", EvaluateView.as_view(), name="graph-evaluate"),
]
