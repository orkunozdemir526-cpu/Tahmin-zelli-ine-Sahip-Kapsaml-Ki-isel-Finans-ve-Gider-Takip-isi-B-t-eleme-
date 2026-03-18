from rest_framework import serializers
from django.contrib.auth.models import User # BUNU EKLEDİK
from .models import Account, Category, Transaction


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'password')
        extra_kwargs = {'password': {'write_only': True}} # Şifre geri okunamaz, sadece yazılır

    def create(self, validated_data):
        # Şifreyi güvenli (hash) olarak kaydetmek için create_user kullanıyoruz
        user = User.objects.create_user(**validated_data)
        return user

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'subcategories']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = '__all__'
        read_only_fields = ['user']

class CategorySerializer(serializers.ModelSerializer):
    # Ağaç yapısındaki alt kategorileri de çekebilmek için
    subcategories = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'parent', 'subcategories']

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'