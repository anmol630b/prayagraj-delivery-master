from rest_framework import serializers
from .models import Category, Product, Cart, Order, OrderItem

class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = '__all__'
    
    def get_image_url(self, obj):
        try:
            if obj.image:
                url = obj.image.url
                if url.startswith('http'):
                    return url
                return f'https://web-production-d08a8.up.railway.app{url}'
        except:
            pass
        return None

class ProductSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_image_url(self, obj):
        try:
            if obj.image:
                url = obj.image.url
                if url.startswith('http'):
                    return url
                return f'https://web-production-d08a8.up.railway.app{url}'
        except:
            pass
        return None

class CartSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.CharField(source='product.price', read_only=True)
    
    class Meta:
        model = Cart
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = '__all__'