from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, ProductViewSet,
    register_user, cart_view, order_view, order_tracking,
    create_payment, verify_payment,
    register_agent, assign_agent, mark_delivered, agent_status
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),

    # Auth
    path('register/', register_user, name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Cart & Orders
    path('cart/', cart_view, name='cart'),
    path('orders/', order_view, name='orders'),
    path('orders/<int:order_id>/tracking/', order_tracking, name='order_tracking'),

    # Payment
    path('payment/create/', create_payment, name='create_payment'),
    path('payment/verify/', verify_payment, name='verify_payment'),

    # Delivery
    path('agent/register/', register_agent, name='register_agent'),
    path('agent/status/', agent_status, name='agent_status'),
    path('orders/<int:order_id>/assign/', assign_agent, name='assign_agent'),
    path('orders/<int:order_id>/delivered/', mark_delivered, name='mark_delivered'),
]