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
from django.conf import settings  # settings'i import et
from django.conf.urls.static import static  # static'i import et

# JWT Views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from users.views import (
    JWTRegistrationAPIView, JWTLogoutAPIView, ChangePasswordAPIView,
    EmailVerificationAPIView, ResendVerificationAPIView, EmailVerificationStatusAPIView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # =============================================================================
    # JWT AUTHENTICATION ENDPOINTS
    # =============================================================================
    # Modern JWT Authentication (access + refresh tokens)
    path('api/auth/register/', JWTRegistrationAPIView.as_view(), name='jwt_register'),
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/logout/', JWTLogoutAPIView.as_view(), name='jwt_logout'),
    path('api/auth/change-password/', ChangePasswordAPIView.as_view(), name='change_password'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Email Verification Endpoints
    path('api/auth/verify-email/', EmailVerificationAPIView.as_view(), name='verify_email'),
    path('api/auth/resend-verification/', ResendVerificationAPIView.as_view(), name='resend_verification'),
    path('api/auth/email-status/', EmailVerificationStatusAPIView.as_view(), name='email_verification_status'),
    
    # =============================================================================
    # USER PROFILE ENDPOINTS  
    # =============================================================================
    # User profile endpoint (for backward compatibility with test scripts)
    path('api/auth-legacy/', include('users.urls', namespace='auth_legacy_api')),
    
    # =============================================================================
    # API ENDPOINTS
    # =============================================================================
    # games uygulamasının URL'lerini /api/games/ ön eki altında dahil et
    path('api/games/', include('games.urls')),
    # path('api/interactions/', include('interactions.urls')),

    # DRF'in login/logout view'larını tarayıcıda görüntülenebilir API için ekleyebiliriz
    # Bu, özellikle /api/auth/login/ endpoint'imiz varken gereksiz olabilir,
    # ancak farklı senaryolar için bilmekte fayda var.
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework_auth_pages'))
]

# Geliştirme ortamında media dosyalarını sunmak için:
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)