from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .email_utils import send_registration_email
from .serializers import UserSerializer


@swagger_auto_schema(
    method='post',
    request_body=UserSerializer,
    responses={201: openapi.Response('Пользователь создан', UserSerializer)},
    operation_description="Регистрация нового пользователя"
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        email = serializer.validated_data.get('email', '')

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Пользователь с таким именем уже существует'},
                            status=status.HTTP_400_BAD_REQUEST)

        if email and User.objects.filter(email=email).exists():
            return Response({'error': 'Пользователь с таким email уже существует'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=request.data.get('password'),
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', '')
        )

        if email:
            send_registration_email(user)

        refresh = RefreshToken.for_user(user)

        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'message': 'Пользователь успешно зарегистрирован'
        }, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['username', 'password'],
        properties={
            'username': openapi.Schema(type=openapi.TYPE_STRING),
            'password': openapi.Schema(type=openapi.TYPE_STRING, format='password'),
        }
    ),
    responses={200: openapi.Response('Успешный вход', UserSerializer)},
    operation_description="Вход пользователя в систему"
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Необходимо указать имя пользователя и пароль'},
                        status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(username=username, password=password)

    if user is None:
        return Response({'error': 'Неверное имя пользователя или пароль'},
                        status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)

    return Response({
        'user': UserSerializer(user).data,
        'tokens': {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        },
        'message': 'Успешный вход'
    })


@swagger_auto_schema(
    method='get',
    responses={200: UserSerializer()},
    operation_description="Получить профиль текущего пользователя"
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_profile(request):
    return Response(UserSerializer(request.user).data)


@swagger_auto_schema(
    method='post',
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['refresh_token'],
        properties={
            'refresh_token': openapi.Schema(type=openapi.TYPE_STRING),
        }
    ),
    responses={200: openapi.Response('Успешный выход')},
    operation_description="Выход пользователя из системы"
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_user(request):
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response({'message': 'Успешный выход'})
    except Exception:
        return Response({'error': 'Неверный токен'}, status=status.HTTP_400_BAD_REQUEST)
