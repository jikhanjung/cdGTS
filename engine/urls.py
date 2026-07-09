from django.urls import path

from .views import EvalJobView, EvaluateView

urlpatterns = [
    path("graphs/<int:pk>/evaluate/", EvaluateView.as_view(), name="graph-evaluate"),
    path("eval-jobs/<int:pk>/", EvalJobView.as_view(), name="eval-job-detail"),
]
