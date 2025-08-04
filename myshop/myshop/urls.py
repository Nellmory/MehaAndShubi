"""
URL configuration for myshop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

from shopapp.telegram_auth import telegram_login_page, telegram_auth_callback, telegram_test_login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shopapp.urls')),
    path('api/', include('shopapp.urls_api')),

    path('telegram/login/', telegram_login_page, name='telegram_login'),
    path('telegram/auth/', telegram_auth_callback, name='telegram_auth'),
    path('telegram/test-login/', telegram_test_login, name='telegram_test_login'),
]