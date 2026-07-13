"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from config.health import healthz

urlpatterns = [
    path('healthz', healthz, name='healthz'),        # 배포 smoke (P08.5)
    path('admin/', admin.site.urls),
    path('api/', include('graph.urls')),
    path('api/', include('nodes.urls')),
    path('api/', include('engine.urls')),
    path('api/', include('releases.urls')),
    path('api/', include('accounts.urls')),
    path('api/', include('references.urls')),
]

# 프론트 SPA(빌드 산출물)가 있으면 루트에서 서빙. dev 는 vite(:5173) 사용.
if settings.FRONTEND_DIST.exists():
    urlpatterns += [path('', TemplateView.as_view(template_name='index.html'), name='spa')]
