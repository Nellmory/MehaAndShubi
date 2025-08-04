from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    CategoryListView, ProductViewSet, ProductDetailView, 
    CartView, OrderView
)
from .auth_views import register_user, login_user, get_user_profile, logout_user

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('auth/register/', register_user, name='api-register'),
    path('auth/login/', login_user, name='api-login'),
    path('auth/profile/', get_user_profile, name='api-profile'),
    path('auth/logout/', logout_user, name='api-logout'),

    path('categories/', CategoryListView.as_view(), name='api-categories'),
    path('', include(router.urls)),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='api-product-detail'),
    path('cart/', CartView.as_view(), name='api-cart'),
    path('order/', OrderView.as_view(), name='api-order'),
] 