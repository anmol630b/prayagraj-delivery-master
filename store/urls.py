from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet,
    register_user, cart_view, order_view, order_tracking,
    create_payment, verify_payment,
    register_agent, assign_agent, mark_delivered, agent_status,
    cancel_order, change_password, chat_messages, saved_addresses, product_ratings, save_fcm_token, wishlist_view, user_profile,
    MyTokenObtainPairView,  # ✅ FIX: custom view use karo
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # ✅ FIX: MyTokenObtainPairView — email bhi return karega
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Auth
    path('register/', register_user, name='register'),

    # Cart & Orders
    path('cart/', cart_view, name='cart'),
    path('orders/', order_view, name='orders'),
    path('orders/<int:order_id>/tracking/', order_tracking, name='order_tracking'),
    path('orders/<int:order_id>/cancel/', cancel_order, name='cancel_order'),

    # Payment
    path('payment/create/', create_payment, name='create_payment'),
    path('payment/verify/', verify_payment, name='verify_payment'),

    # Delivery
    path('agent/register/', register_agent, name='register_agent'),
    path('agent/status/', agent_status, name='agent_status'),
    path('orders/<int:order_id>/assign/', assign_agent, name='assign_agent'),
    path('orders/<int:order_id>/delivered/', mark_delivered, name='mark_delivered'),

    # Account
    path('change-password/', change_password, name='change_password'),
    path('chat/', chat_messages, name='chat'),
    path('addresses/', saved_addresses, name='addresses'),
    path('addresses/<int:address_id>/', saved_addresses, name='address_detail'),
    path('products/<int:product_id>/ratings/', product_ratings, name='product_ratings'),
    path('fcm-token/', save_fcm_token, name='save_fcm_token'),
    path('wishlist/', wishlist_view, name='wishlist'),
    path('wishlist/<int:product_id>/', wishlist_view, name='wishlist_detail'),
    path('profile/', user_profile, name='user_profile'),
]
