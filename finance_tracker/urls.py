from django.contrib import admin
from django.urls import path, include
# JWT Token uç noktalarını (endpoints) içeri aktarıyoruz
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # GÜVENLİK: Kullanıcının giriş yapıp (login) JWT Token alacağı rotalar
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Bizim yazdığımız uygulamanın API rotaları
    path('api/', include('tracker.urls')), 
]