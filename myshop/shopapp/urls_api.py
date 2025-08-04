from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    CategoryListView, ProductViewSet, ProductDetailView, 
    CartView, OrderView
)

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='api-categories'),
    path('', include(router.urls)),
    path('product/<int:pk>/', ProductDetailView.as_view(), name='api-product-detail'),
    path('cart/', CartView.as_view(), name='api-cart'),
    path('order/', OrderView.as_view(), name='api-order'),
] 