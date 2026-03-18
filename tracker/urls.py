from django.urls import path, include
from rest_framework.routers import DefaultRouter
# RegisterAPIView eklendi
from .views import AccountViewSet, CategoryViewSet, TransactionViewSet, ForecastAPIView, CurrencyConversionAPIView, TransactionExportCSVView, RegisterAPIView

router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'transactions', TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterAPIView.as_view(), name='register'), # YENİ KAYIT ROTASI
    path('forecast/', ForecastAPIView.as_view(), name='forecast'),
    path('convert/', CurrencyConversionAPIView.as_view(), name='convert'), 
    path('export/csv/', TransactionExportCSVView.as_view(), name='export_csv'),
]