"""
URL configuration for gamehost_project project.

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
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # games uygulamasının URL'lerini /api/games/ ön eki altında dahil et
    path('api/games/', include('games.urls')),
    # İleride users ve interactions için de benzer path'ler ekleyeceğiz:
    # path('api/users/', include('users.urls')),
    # path('api/interactions/', include('interactions.urls')),

    # DRF'in login/logout view'larını tarayıcıda görüntülenebilir API için ekleyebiliriz (isteğe bağlı)
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
