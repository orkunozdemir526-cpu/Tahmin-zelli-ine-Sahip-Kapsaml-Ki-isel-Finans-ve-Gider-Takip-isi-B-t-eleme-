import math
from datetime import datetime, timedelta

class ExpenseForecaster:
    """
    Zaman serisi analizi ve Doğrusal Regresyon kullanarak gelecekteki 
    harcamaları tahmin eden (Predictive Budgeting) analitik sınıfı.
    """
    def __init__(self, transactions):
        self.transactions = sorted(transactions, key=lambda t: t.date)
        self.n = len(self.transactions)
        
        self.x_data = [] 
        self.y_data = [] 
        
        self.slope = 0.0      
        self.intercept = 0.0  
        self.variance = 0.0
        self.std_dev = 0.0

        if self.n > 1:
            self._prepare_data()
            self._calculate_regression()
            self._calculate_variance()

    def _prepare_data(self):
        """Tarihleri başlangıç gününden itibaren geçen gün sayısına (x) çevirir."""
        if not self.transactions:
            return
            
        start_date = self.transactions[0].date.date()
        for t in self.transactions:
            if t.transaction_type == 'EXPENSE':
                days_passed = (t.date.date() - start_date).days
                self.x_data.append(days_passed)
                self.y_data.append(float(t.amount))
        
        self.n = len(self.x_data)

    def _calculate_regression(self):
        """En Küçük Kareler Yöntemi ile regresyon katsayılarını hesaplar."""
        if self.n < 2:
            return

        sum_x = sum(self.x_data)
        sum_y = sum(self.y_data)
        sum_xy = sum(x * y for x, y in zip(self.x_data, self.y_data))
        sum_x_squared = sum(x ** 2 for x in self.x_data)

        denominator = (self.n * sum_x_squared) - (sum_x ** 2)
        if denominator == 0:
            self.slope = 0
        else:
            self.slope = ((self.n * sum_xy) - (sum_x * sum_y)) / denominator

        self.intercept = (sum_y - (self.slope * sum_x)) / self.n

    def _calculate_variance(self):
        """Tahminlerin güvenilirliğini ölçmek için varyans ve standart sapma hesaplar."""
        if self.n < 2:
            return
            
        sse = 0 
        for x, y in zip(self.x_data, self.y_data):
            y_pred = self.intercept + (self.slope * x)
            sse += (y - y_pred) ** 2
            
        self.variance = sse / (self.n - 1)  
        self.std_dev = math.sqrt(self.variance)

    def predict_future_expenses(self, target_date):
        """Belirtilen hedef tarih için tahmini harcama miktarını döndürür."""
        if self.n < 2 or not self.transactions:
            return None
            
        start_date = self.transactions[0].date.date()
        
        if hasattr(target_date, 'date'):
            target_date = target_date.date()

        target_days_passed = (target_date - start_date).days
        
        predicted_amount = self.intercept + (self.slope * target_days_passed)
        predicted_amount = max(0.0, predicted_amount)
        
        return {
            'target_date': target_date.strftime('%Y-%m-%d'),
            'predicted_amount': round(predicted_amount, 2),
            'lower_bound': round(max(0.0, predicted_amount - self.std_dev), 2),
            'upper_bound': round(predicted_amount + self.std_dev, 2)
        }