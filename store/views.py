from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Category, Product, Cart, Order, OrderItem
from .serializers import CategorySerializer, ProductSerializer, CartSerializer, OrderSerializer
from .notifications import send_order_notification
import razorpay
import os

# Razorpay client
razorpay_client = razorpay.Client(
    auth=(os.environ.get('RAZORPAY_KEY_ID'), os.environ.get('RAZORPAY_KEY_SECRET'))
)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    
    user = User.objects.create_user(username=username, password=password, email=email)
    return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def cart_view(request):
    if request.method == 'GET':
        cart = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        product_id = request.data.get('product')
        quantity = request.data.get('quantity', 1)
        product = Product.objects.get(id=product_id)
        cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
        cart_item.quantity = quantity
        cart_item.save()
        return Response({'message': 'Added to cart'}, status=status.HTTP_201_CREATED)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_view(request):
    if request.method == 'GET':
        orders = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        total = sum(item.product.price * item.quantity for item in cart_items)
        address = request.data.get('address', '')
        
        order = Order.objects.create(user=request.user, total_price=total, address=address)
        
        for item in cart_items:
            OrderItem.objects.create(order=order, product=item.product, quantity=item.quantity, price=item.product.price)
        
        cart_items.delete()

        fcm_token = request.data.get('fcm_token')
        if fcm_token:
            send_order_notification(
                fcm_token=fcm_token,
                title="Order Placed! 🎉",
                body=f"Aapka order #{order.id} successfully place ho gaya!"
            )

        return Response({'message': 'Order placed successfully', 'order_id': order.id}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_tracking(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        return Response({
            'order_id': order.id,
            'status': order.status,
            'address': order.address,
            'total_price': str(order.total_price),
            'created_at': order.created_at,
            'status_steps': {
                'pending': order.status in ['pending', 'confirmed', 'delivered'],
                'confirmed': order.status in ['confirmed', 'delivered'],
                'delivered': order.status == 'delivered',
            }
        })
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    amount = request.data.get('amount')
    
    order_data = {
        'amount': int(amount) * 100,  # Razorpay paise mein leta hai
        'currency': 'INR',
        'payment_capture': 1
    }
    
    razorpay_order = razorpay_client.order.create(order_data)
    
    return Response({
        'order_id': razorpay_order['id'],
        'amount': amount,
        'currency': 'INR',
        'key': os.environ.get('RAZORPAY_KEY_ID')
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    payment_id = request.data.get('razorpay_payment_id')
    order_id = request.data.get('razorpay_order_id')
    signature = request.data.get('razorpay_signature')
    
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
        return Response({'message': 'Payment verified! ✅', 'status': 'success'})
    except:
        return Response({'message': 'Payment failed ❌', 'status': 'failed'}, status=400)