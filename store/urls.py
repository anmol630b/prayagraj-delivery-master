from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, register_user, cart_view, order_view, order_tracking

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', register_user, name='register'),
    path('cart/', cart_view, name='cart'),
    path('orders/', order_view, name='orders'),
    path('orders/<int:order_id>/tracking/', order_tracking, name='order_tracking'),
]