from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import Category, Product, Cart, Order, OrderItem, DeliveryAgent, DeliveryAssignment, ChatMessage, SavedAddress, Rating, FCMToken, Wishlist, UserProfile
from .serializers import CategorySerializer, ProductSerializer, CartSerializer, OrderSerializer
from .notifications import send_order_notification
from django.utils import timezone
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
import razorpay
import os

razorpay_client = razorpay.Client(
    auth=(os.environ.get('RAZORPAY_KEY_ID'), os.environ.get('RAZORPAY_KEY_SECRET'))
)

# ✅ FIX 1: Custom JWT token jo email bhi return kare
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['email'] = self.user.email        # email add kiya
        data['username'] = self.user.username  # username bhi
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.filter(is_available=True)
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__id=category)
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        sort = self.request.query_params.get('sort')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        return queryset

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email    = request.data.get('email')
    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)
    User.objects.create_user(username=username, password=password, email=email)
    return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)

@api_view(['GET', 'POST', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def cart_view(request):
    if request.method == 'GET':
        cart_items = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(cart_items, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        product_id = request.data.get('product')
        quantity   = request.data.get('quantity', 1)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product nahi mila'}, status=404)
        cart_item, created = Cart.objects.get_or_create(
            user=request.user, product=product,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        serializer = CartSerializer(cart_item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    elif request.method == 'PATCH':
        cart_id  = request.data.get('cart_id')
        quantity = request.data.get('quantity')
        try:
            cart_item          = Cart.objects.get(id=cart_id, user=request.user)
            cart_item.quantity = quantity
            cart_item.save()
            return Response({'status': 'updated'})
        except Cart.DoesNotExist:
            return Response({'error': 'Cart item nahi mila'}, status=404)

    elif request.method == 'DELETE':
        cart_id = request.data.get('cart_id')
        try:
            cart_item = Cart.objects.get(id=cart_id, user=request.user)
            cart_item.delete()
            return Response({'status': 'deleted'})
        except Cart.DoesNotExist:
            return Response({'error': 'Cart item nahi mila'}, status=404)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def order_view(request):
    if request.method == 'GET':
        orders     = Order.objects.filter(user=request.user).order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        # COD payment system
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items:
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

        total   = sum(item.product.price * item.quantity for item in cart_items)
        address = request.data.get('address', '')
        order   = Order.objects.create(user=request.user, total_price=total, address=address)

        for item in cart_items:
            OrderItem.objects.create(
                order=order, product=item.product,
                quantity=item.quantity, price=item.product.price
            )
        cart_items.delete()

        fcm_token = request.data.get('fcm_token')
        if fcm_token:
            send_order_notification(
                fcm_token=fcm_token,
                title="Order Placed! 🎉",
                body=f"Aapka order #{order.id} successfully place ho gaya!"
            )
        return Response(
            {'message': 'Order placed successfully', 'order_id': order.id},
            status=status.HTTP_201_CREATED
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order nahi mila'}, status=404)
    if order.status != 'pending':
        return Response(
            {'error': f'Order cancel nahi ho sakta. Current status: {order.status}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    order.status = 'cancelled'
    order.save()
    return Response({'message': f'Order #{order.id} cancel ho gaya ✅'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    old_password = request.data.get('old_password')
    new_password = request.data.get('new_password')
    if not old_password or not new_password:
        return Response({'error': 'Dono passwords required hain'}, status=400)
    user = request.user
    if not user.check_password(old_password):
        return Response({'error': 'Purana password galat hai ❌'}, status=400)
    if len(new_password) < 6:
        return Response({'error': 'Naya password kam se kam 6 characters ka hona chahiye'}, status=400)
    user.set_password(new_password)
    user.save()
    return Response({'message': 'Password change ho gaya! ✅'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_tracking(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)
        return Response({
            'order_id':    order.id,
            'status':      order.status,
            'address':     order.address,
            'total_price': str(order.total_price),
            'created_at':  order.created_at,
            'status_steps': {
                'pending':          order.status in ['pending', 'confirmed', 'out_for_delivery', 'delivered'],
                'confirmed':        order.status in ['confirmed', 'out_for_delivery', 'delivered'],
                'out_for_delivery': order.status in ['out_for_delivery', 'delivered'],
                'delivered':        order.status == 'delivered',
            }
        })
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment(request):
    amount = request.data.get('amount')
    order_data = {
        'amount':          int(amount) * 100,
        'currency':        'INR',
        'payment_capture': 1
    }
    razorpay_order = razorpay_client.order.create(order_data)
    return Response({
        'order_id': razorpay_order['id'],
        'amount':   amount,
        'currency': 'INR',
        'key':      os.environ.get('RAZORPAY_KEY_ID')
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment(request):
    payment_id = request.data.get('razorpay_payment_id')
    order_id   = request.data.get('razorpay_order_id')
    signature  = request.data.get('razorpay_signature')
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id':   order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature':  signature
        })
        return Response({'message': 'Payment verified! ✅', 'status': 'success'})
    except:
        return Response({'message': 'Payment failed ❌', 'status': 'failed'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_agent(request):
    phone = request.data.get('phone')
    if DeliveryAgent.objects.filter(user=request.user).exists():
        return Response({'error': 'Agent already registered'}, status=400)
    agent = DeliveryAgent.objects.create(user=request.user, phone=phone)
    return Response({'message': 'Delivery agent registered! ✅', 'agent_id': agent.id})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_agent(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        agent = DeliveryAgent.objects.filter(is_available=True).first()
        if not agent:
            return Response({'error': 'Koi agent available nahi hai'}, status=400)
        assignment         = DeliveryAssignment.objects.create(order=order, agent=agent)
        agent.is_available = False
        agent.save()
        order.status       = 'out_for_delivery'
        order.save()
        return Response({
            'message':       f'Agent {agent.user.username} assigned! 🚴',
            'assignment_id': assignment.id
        })
    except Order.DoesNotExist:
        return Response({'error': 'Order nahi mila'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_delivered(request, order_id):
    try:
        assignment                    = DeliveryAssignment.objects.get(order__id=order_id)
        assignment.delivered_at       = timezone.now()
        assignment.save()
        assignment.agent.is_available = True
        assignment.agent.save()
        assignment.order.status       = 'delivered'
        assignment.order.save()
        return Response({'message': 'Order delivered! 🎉'})
    except DeliveryAssignment.DoesNotExist:
        return Response({'error': 'Assignment nahi mila'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def agent_status(request):
    try:
        agent = DeliveryAgent.objects.get(user=request.user)
        return Response({
            'agent':            agent.user.username,
            'phone':            agent.phone,
            'is_available':     agent.is_available,
            'current_location': agent.current_location,
        })
    except DeliveryAgent.DoesNotExist:
        return Response({'error': 'Agent nahi mila'}, status=404)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def chat_messages(request):
    if request.method == 'GET':
        messages = ChatMessage.objects.filter(user=request.user).order_by('created_at')
        data = [{
            'id': m.id,
            'message': m.message,
            'is_admin': m.is_admin,
            'created_at': m.created_at.strftime('%H:%M'),
        } for m in messages]
        return Response(data)

    elif request.method == 'POST':
        message = request.data.get('message', '').strip()
        if not message:
            return Response({'error': 'Message khali hai!'}, status=400)
        msg = ChatMessage.objects.create(
            user=request.user,
            message=message,
            is_admin=False
        )
        return Response({
            'id': msg.id,
            'message': msg.message,
            'is_admin': False,
            'created_at': msg.created_at.strftime('%H:%M'),
        }, status=201)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def saved_addresses(request, address_id=None):
    if request.method == 'GET':
        addresses = SavedAddress.objects.filter(user=request.user).order_by('-is_default', '-created_at')
        data = [{'id': a.id, 'label': a.label, 'address': a.address, 'is_default': a.is_default} for a in addresses]
        return Response(data)

    elif request.method == 'POST':
        label = request.data.get('label', 'Ghar')
        address = request.data.get('address', '').strip()
        is_default = request.data.get('is_default', False)
        if not address:
            return Response({'error': 'Address khali hai!'}, status=400)
        if is_default:
            SavedAddress.objects.filter(user=request.user).update(is_default=False)
        addr = SavedAddress.objects.create(
            user=request.user, label=label, address=address, is_default=is_default)
        return Response({'id': addr.id, 'label': addr.label, 'address': addr.address, 'is_default': addr.is_default}, status=201)

    elif request.method == 'PUT':
        addr = SavedAddress.objects.filter(id=address_id, user=request.user).first()
        if not addr:
            return Response({'error': 'Address nahi mila!'}, status=404)
        if request.data.get('is_default'):
            SavedAddress.objects.filter(user=request.user).update(is_default=False)
        addr.label = request.data.get('label', addr.label)
        addr.address = request.data.get('address', addr.address)
        addr.is_default = request.data.get('is_default', addr.is_default)
        addr.save()
        return Response({'id': addr.id, 'label': addr.label, 'address': addr.address, 'is_default': addr.is_default})

    elif request.method == 'DELETE':
        addr = SavedAddress.objects.filter(id=address_id, user=request.user).first()
        if not addr:
            return Response({'error': 'Address nahi mila!'}, status=404)
        addr.delete()
        return Response({'message': 'Address delete ho gaya!'})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def product_ratings(request, product_id):
    if request.method == 'GET':
        ratings = Rating.objects.filter(product_id=product_id).order_by('-created_at')
        data = [{
            'id': r.id,
            'username': r.user.username,
            'stars': r.stars,
            'review': r.review,
            'created_at': r.created_at.strftime('%d %b %Y'),
        } for r in ratings]
        avg = sum(r['stars'] for r in data) / len(data) if data else 0
        return Response({'average': round(avg, 1), 'total': len(data), 'ratings': data})

    elif request.method == 'POST':
        stars = request.data.get('stars', 5)
        review = request.data.get('review', '')
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({'error': 'Order ID chahiye!'}, status=400)
        order = Order.objects.filter(id=order_id, user=request.user, status='delivered').first()
        if not order:
            return Response({'error': 'Delivered order nahi mila!'}, status=400)
        if Rating.objects.filter(user=request.user, product_id=product_id, order=order).exists():
            return Response({'error': 'Pehle se rating de chuke ho!'}, status=400)
        rating = Rating.objects.create(
            user=request.user,
            product_id=product_id,
            order=order,
            stars=stars,
            review=review
        )
        return Response({'message': 'Rating de di!', 'id': rating.id}, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_fcm_token(request):
    token = request.data.get('token', '').strip()
    if not token:
        return Response({'error': 'Token khali hai!'}, status=400)
    FCMToken.objects.get_or_create(user=request.user, token=token)
    return Response({'message': 'Token save ho gaya!'})


@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_view(request, product_id=None):
    if request.method == 'GET':
        items = Wishlist.objects.filter(user=request.user).select_related('product')
        data = [{
            'id': w.id,
            'product_id': w.product.id,
            'name': w.product.name,
            'price': str(w.product.price),
            'image': w.product.image,
        } for w in items]
        return Response(data)

    elif request.method == 'POST':
        product = Product.objects.filter(id=product_id).first()
        if not product:
            return Response({'error': 'Product nahi mila!'}, status=404)
        w, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if created:
            return Response({'message': 'Wishlist mein add ho gaya!', 'wishlisted': True}, status=201)
        return Response({'message': 'Pehle se wishlist mein hai!', 'wishlisted': True})

    elif request.method == 'DELETE':
        Wishlist.objects.filter(user=request.user, product_id=product_id).delete()
        return Response({'message': 'Wishlist se remove ho gaya!', 'wishlisted': False})


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'GET':
        return Response({
            'username': request.user.username,
            'email': request.user.email,
            'phone': profile.phone,
            'avatar_url': profile.avatar_url,
        })
    
    elif request.method == 'POST':
        profile.phone = request.data.get('phone', profile.phone)
        profile.avatar_url = request.data.get('avatar_url', profile.avatar_url)
        request.user.email = request.data.get('email', request.user.email)
        request.user.first_name = request.data.get('first_name', request.user.first_name)
        request.user.save()
        profile.save()
        return Response({'message': 'Profile updated!'})
