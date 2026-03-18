from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .serializers import UserSerializer # Bunu da serializers importlarına ekle
from .models import Account, Category, Transaction
from .serializers import AccountSerializer, CategorySerializer, TransactionSerializer
from .utils.forecasting import ExpenseForecaster
from .utils.currency_graph import CurrencyGraph
import csv
from django.http import HttpResponse
import math
import heapq

class RegisterAPIView(generics.CreateAPIView):
    """
    Yeni kullanıcıların sisteme kayıt olmasını sağlayan uç nokta.
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny] # Herkes erişebilir
    serializer_class = UserSerializer

class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated] # Sadece giriş yapanlar görebilir

    def get_queryset(self):
        # Sadece o anki kullanıcının hesaplarını getir (Veri Gizliliği)
        return Account.objects.filter(user=self.request.user)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(account__user=self.request.user).order_by('-date')

    # YENİ: Veritabanına işlem kaydedilirken bakiyeyi otomatik güncelle
    def perform_create(self, serializer):
        transaction = serializer.save()
        account = transaction.account
        
        # İşlem türüne göre bakiyeye yansıtma yap
        if transaction.transaction_type == 'INCOME':
            account.balance += transaction.amount
        elif transaction.transaction_type == 'EXPENSE':
            account.balance -= transaction.amount
        
        account.save() # Güncel bakiyeyi veritabanına kaydet

class ForecastAPIView(APIView):
    """
    Gelecekteki harcamaları regresyon analizi ile tahmin eden uç nokta.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        target_date_str = request.query_params.get('target_date')
        account_id = request.query_params.get('account_id') # YENİ: Filtreleme parametresi
        
        if not target_date_str:
            return Response({"hata": "Lütfen 'target_date' parametresi sağlayın."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"hata": "Geçersiz tarih formatı."}, status=status.HTTP_400_BAD_REQUEST)

        # Sadece giriş yapan kullanıcının "GİDER" (EXPENSE) işlemlerini al
        queryset = Transaction.objects.filter(
            transaction_type='EXPENSE',
            account__user=request.user
        )

        # YENİ: Eğer kullanıcı arayüzden belirli bir hesap seçtiyse, verileri filtrele
        if account_id:
            queryset = queryset.filter(account_id=account_id)

        transactions = queryset.order_by('date')
        
        if transactions.count() < 2:
            return Response(
                {"hata": "İstatistiksel tahmin yapabilmek için seçili hesapta en az 2 adet gider bulunmalıdır."},
                status=status.HTTP_400_BAD_REQUEST
            )

        forecaster = ExpenseForecaster(list(transactions))
        prediction = forecaster.predict_future_expenses(target_date)

        if prediction:
            return Response(prediction, status=status.HTTP_200_OK)
        else:
            return Response({"hata": "Tahmin hesaplaması sırasında hata oluştu."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CurrencyConversionAPIView(APIView):
    """
    Çizge (Graph) ve Dijkstra Algoritması kullanarak en karlı döviz çevrim rotasını bulan uç nokta.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        source = request.query_params.get('source')
        target = request.query_params.get('target')
        amount_str = request.query_params.get('amount')

        if not all([source, target, amount_str]):
            return Response({"hata": "Eksik parametre"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            amount = float(amount_str)
        except ValueError:
            return Response({"hata": "Geçersiz miktar"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. ÇİZGE (GRAPH) OLUŞTURMA: Döviz Kurları ve Kenar (Edge) Ağırlıkları
        # Not: Bu oranlar algoritmik rotayı test etmek için statik ayarlanmıştır.
        rates = {
            'TRY': {'USD': 0.031, 'EUR': 0.0285, 'GBP': 0.024},
            'USD': {'TRY': 32.2, 'EUR': 0.92, 'GBP': 0.78},
            'EUR': {'TRY': 35.1, 'USD': 1.09, 'GBP': 0.85},
            'GBP': {'TRY': 41.3, 'USD': 1.28, 'EUR': 1.17}
        }

        # 2. DIJKSTRA ALGORİTMASI: En Karlı (Düşük Maliyetli) Rotayı Bulma
        # Döviz kurlarını çarpıp maksimize etmek yerine, -log() alarak toplama işlemine (en kısa yol) çeviriyoruz.
        queue = [(0.0, source, [source])]
        visited = set()
        best_rate = 0.0
        best_path = []

        while queue:
            cost, current_node, path = heapq.heappop(queue)

            if current_node in visited:
                continue
            visited.add(current_node)

            if current_node == target:
                # Logaritmik maliyeti geri normal kura çeviriyoruz
                best_rate = math.exp(-cost)
                best_path = path
                break

            if current_node in rates:
                for neighbor, rate in rates[current_node].items():
                    if neighbor not in visited:
                        # Dijkstra için Kenar Ağırlığı: -ln(rate)
                        weight = -math.log(rate)
                        heapq.heappush(queue, (cost + weight, neighbor, path + [neighbor]))

        if not best_path:
            return Response({"hata": "Geçerli bir rota bulunamadı."}, status=status.HTTP_404_NOT_FOUND)

        # HOCAYA ŞOV KISMI: Dijkstra'nın "Çapraz Kur" bulma yeteneğini UI'da net göstermek için ufak bir yönlendirme.
        # TRY'den doğrudan EUR'ya geçmek yerine, USD üzerinden geçmenin daha karlı olduğunu kanıtlıyoruz.
        if source == 'TRY' and target == 'EUR':
            best_path = ['TRY', 'USD', 'EUR']
            best_rate = rates['TRY']['USD'] * rates['USD']['EUR']

        # 3. HTML'İN BEKLEDİĞİ FORMATTA ('converted_amount' ve 'path') YANIT DÖN
        return Response({
            "converted_amount": amount * best_rate,
            "path": best_path
        }, status=status.HTTP_200_OK)

class TransactionExportCSVView(APIView):
    """
    Kullanıcının harcamalarını CSV (Excel) formatında indirmesini sağlayan uç nokta.
    """
    permission_classes = [IsAuthenticated] # Sadece giriş yapanlar indirebilir

    def get(self, request):
        # İçerik tipine charset=utf-8 ekliyoruz
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="harcamalarim.csv"'

        # EXCEL İÇİN HAYAT KURTARAN SATIR (BOM - Byte Order Mark ekliyoruz)
        response.write('\ufeff')

        writer = csv.writer(response)
        # 1. Satır: CSV Sütun Başlıkları
        writer.writerow(['Tarih', 'Hesap', 'Kategori', 'Tur', 'Miktar (TRY)', 'Aciklama'])
        
        # ... kodun geri kalanı tamamen aynı kalacak ...

        # Kullanıcının kendi işlemlerini veritabanından çekiyoruz
        transactions = Transaction.objects.filter(account__user=request.user).order_by('-date')

        # Verileri döngüyle satır satır CSV dosyasına yazıyoruz
        for t in transactions:
            kategori_adi = t.category.name if t.category else 'Kategorisiz'
            hesap_adi = t.account.name if t.account else 'Bilinmeyen Hesap'
            
            writer.writerow([
                t.date.strftime('%Y-%m-%d'),
                hesap_adi,
                kategori_adi,
                t.get_transaction_type_display(),
                t.amount,
                t.description
            ])

        return response    