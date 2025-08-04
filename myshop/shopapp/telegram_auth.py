import hashlib
import hmac
import time
from venv import logger

from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework_simplejwt.tokens import RefreshToken

# Конфигурация Telegram бота
BOT_TOKEN = '8391475114:AAFohXo9zR9AZpaVqv8iHHgehgtzTUiqKYg'
BOT_USERNAME = 'MehaAndShubiBot'


def verify_telegram_data(data):
    if 'hash' not in data:
        return False

    auth_data = data.copy()
    received_hash = auth_data.pop('hash')

    data_check_arr = ['{}={}'.format(k, v) for k, v in sorted(auth_data.items())]
    data_check_string = '\n'.join(data_check_arr)

    secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

    return computed_hash == received_hash


def get_or_create_user_from_telegram(telegram_data):
    telegram_id = telegram_data.get('id')
    username = f"tg_{telegram_id}"

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_user(
            username=username,
            first_name=telegram_data.get('first_name', ''),
            last_name=telegram_data.get('last_name', '')
        )

        if 'username' in telegram_data:
            user.email = f"{telegram_data['username']}@telegram.com"
            user.save()

    return user


def telegram_login_page(request):
    context = {
        'bot_username': BOT_USERNAME,
        'callback_url': request.build_absolute_uri('/telegram/auth/'),
    }
    return render(request, 'telegram_auth/telegram_login.html', context)


@csrf_exempt
def telegram_auth_callback(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается'}, status=405)

    telegram_data = request.POST.dict()

    if not verify_telegram_data(telegram_data):
        return JsonResponse({'error': 'Неверные данные аутентификации'}, status=400)

    auth_date = int(telegram_data.get('auth_date', 0))
    current_time = int(time.time())
    if current_time - auth_date > 3600:
        return JsonResponse({'error': 'Данные аутентификации устарели'}, status=400)

    try:
        user = get_or_create_user_from_telegram(telegram_data)

        login(request, user)

        refresh = RefreshToken.for_user(user)

        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'telegram_id': telegram_data.get('id'),
            },
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def telegram_test_login(request):
    if request.method == 'POST':
        try:
            # Получаем данные из запроса
            telegram_id = request.POST.get('telegram_id', '12345678')
            first_name = request.POST.get('first_name', 'Тестовый')
            last_name = request.POST.get('last_name', 'Пользователь')
            username = request.POST.get('username', 'test_user')

            logger.info(
                f"Получены данные: ID={telegram_id}, имя={first_name}, фамилия={last_name}, username={username}")

            # Создаем или получаем пользователя
            user_name = f"tg_{telegram_id}"
            try:
                user = User.objects.get(username=user_name)
                logger.info(f"Найден существующий пользователь: {user.username}")
            except User.DoesNotExist:
                logger.info(f"Создаем нового пользователя: {user_name}")
                user = User.objects.create_user(
                    username=user_name,
                    first_name=first_name,
                    last_name=last_name
                )
                if username:
                    user.email = f"{username}@telegram.com"
                    user.save()

            # Авторизуем пользователя
            login(request, user)
            logger.info(f"Пользователь {user.username} авторизован")

            # Создаем JWT токены
            refresh = RefreshToken.for_user(user)

            return JsonResponse({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'telegram_id': telegram_id,
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            })
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return render(request, 'telegram_auth/telegram_test_login.html')