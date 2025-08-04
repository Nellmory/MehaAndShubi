from rest_framework import generics, viewsets, permissions, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .email_utils import send_order_confirmation_email
from .models import Category, Product, Cart, CartItem, Order, OrderItem
from .serializers import (
    CategorySerializer, ProductSerializer, CartSerializer, CartItemSerializer, CartItemCreateSerializer,
    OrderSerializer, OrderCreateSerializer
)
from django.shortcuts import get_object_or_404


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(parent=None)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['name', 'description', 'characteristics']
    ordering_fields = ['price', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        return queryset

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('min_price', openapi.IN_QUERY, description="Минимальная цена", type=openapi.TYPE_NUMBER),
            openapi.Parameter('max_price', openapi.IN_QUERY, description="Максимальная цена", type=openapi.TYPE_NUMBER),
        ],
        operation_description="Получить список товаров с фильтрацией"
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['category'],
            properties={
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID категории"),
            }
        ),
        operation_description="Получить товары по категории",
        responses={200: ProductSerializer(many=True)}
    )
    @action(detail=False, methods=['post'], url_path='by-category')
    def by_category(self, request):
        category_id = request.data.get('category')
        if not category_id:
            return Response({'error': 'category required'}, status=400)
        products = self.get_queryset().filter(category_id=category_id)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'pk'


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получить корзину текущего пользователя",
        responses={200: CartSerializer()}
    )
    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description="Добавить товар в корзину",
        request_body=CartItemCreateSerializer,
        responses={200: CartSerializer()}
    )
    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data['product']
        quantity = serializer.validated_data['quantity']
        item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            item.quantity += quantity
        else:
            item.quantity = quantity
        item.save()
        return Response(CartSerializer(cart).data)

    @swagger_auto_schema(
        operation_description="Изменить количество товара в корзине",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['item_id', 'quantity'],
            properties={
                'item_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'quantity': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1),
            }
        ),
        responses={200: CartSerializer()}
    )
    def put(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.quantity = quantity
        item.save()
        return Response(CartSerializer(cart).data)

    @swagger_auto_schema(
        operation_description="Удалить товар из корзины",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['item_id'],
            properties={
                'item_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        ),
        responses={200: CartSerializer()}
    )
    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item_id = request.data.get('item_id')
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        return Response(CartSerializer(cart).data)


class OrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Создать заказ из товаров в корзине",
        request_body=OrderCreateSerializer,
        responses={200: OrderSerializer()}
    )
    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.exists():
            return Response({'error': 'Корзина пуста'}, status=400)
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = Order.objects.create(
            user=request.user,
            shipping_address=serializer.validated_data['shipping_address'],
            phone=serializer.validated_data['phone'],
            total_price=cart.total_price
        )
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )
        cart.items.all().delete()

        if request.user.email:
            send_order_confirmation_email(order)

        return Response(OrderSerializer(order).data)

    @swagger_auto_schema(
        operation_description="Получить список заказов текущего пользователя",
        responses={200: OrderSerializer(many=True)}
    )
    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
