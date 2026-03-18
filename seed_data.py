import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'finance_tracker.settings')
django.setup()

from tracker.models import Category
from django.contrib.auth.models import User

def seed_categories():
    # Eski karmaşık kategorileri temizliyoruz
    Category.objects.all().delete()

    # Sadeleştirilmiş, net ana kategoriler
    kategoriler = [
        'Faturalar',          # Elektrik, Su, İnternet vs. açıklamaya yazılacak
        'Market & Gıda',      # Çakışmayı önlemek için birleştirildi
        'Kafe & Restoran',
        'Ulaşım',             # Akaryakıt, Otobüs, Taksi
        'Eğitim',
        'Kişisel Bakım',
        'Eğlence',
        'Diğer'
    ]

    for kat in kategoriler:
        Category.objects.create(name=kat)
        print(f"Kategori eklendi: {kat}")

    print("--- Kategoriler başarıyla güncellendi! ---")

if __name__ == '__main__':
    seed_categories()