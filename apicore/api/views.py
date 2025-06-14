from django.shortcuts import render
from rest_framework import generics
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

import hmac
import hashlib
import json
from urllib.parse import parse_qsl, unquote
from django.conf import settings
from .models import *
from .serializer import *
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny

class PostApiList(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class PostApiUpdate(generics.UpdateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class CategoryApiList(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticated, )

class CategoryApiUpdate(generics.UpdateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

@method_decorator(csrf_exempt, name='dispatch')
class TelegramAuthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            # Логирование для отладки
            print(f"Request method: {request.method}")
            print(f"Request headers: {dict(request.headers)}")
            print(f"Request data: {request.data}")
            
            init_data = request.data.get("initData", "")
            if not init_data:
                return Response({
                    "auth": False, 
                    "token": "", 
                    "error": "initData is required"
                }, status=400)

            # Парсим данные от Telegram
            data_dict = dict(parse_qsl(init_data, keep_blank_values=True))
            hash_from_telegram = data_dict.pop("hash", None)

            if not hash_from_telegram:
                return Response({
                    "auth": False, 
                    "token": "", 
                    "error": "hash is missing"
                }, status=400)

            if not hasattr(settings, 'BOT_TOKEN'):
                return Response({
                    "auth": False, 
                    "token": "", 
                    "error": "BOT_TOKEN not configured on server"
                }, status=500)

            # Формируем check_string по официальной документации Telegram
            # Сортируем по ключам и соединяем через \n
            check_string = "\n".join([f"{k}={v}" for k, v in sorted(data_dict.items())])
            print(f"Check string for hash: {repr(check_string)}")

            # Создаем секретный ключ согласно документации
            secret_key = hmac.new(b"WebAppData", settings.BOT_TOKEN.encode(), hashlib.sha256).digest()
            hmac_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

            if hmac_hash != hash_from_telegram:
                print(f"Hash mismatch. Expected: {hmac_hash}, Got: {hash_from_telegram}")
                print(f"Check string: {check_string}")
                return Response({
                    "auth": False, 
                    "token": "", 
                    "error": "Invalid signature"
                }, status=403)
            
            # return Response({
            #     "auth": True
            # }, status=200)
            print(f"Check is OK")
            # Получаем данные пользователя
            user_data_str = data_dict.get("user", "")
            if not user_data_str:
                return Response({
                    "auth": False, 
                    "token": "", 
                    "error": "user data is missing"
                }, status=400)
            
            # Парсинг JSON
            try:
                user_data = json.loads(user_data_str)
            except json.JSONDecodeError:
                return Response({
                    "auth": False, 
                    "token": "", 
                    "error": "Invalid user data format"
                }, status=400)
            
            telegram_id = user_data.get("id")
            username = user_data.get("username", f"user_{telegram_id}")
            first_name = user_data.get("first_name", username)
            
            if not telegram_id:
                return Response({
                    "auth": False, 
                    "token": "", 
                    "error": "telegram id is missing"
                }, status=400)
            
            # Создаем или получаем пользователя
            user, created = User.objects.get_or_create(
                username=str(telegram_id),
                defaults={
                    "first_name": first_name,
                    "is_active": True
                }
            )
            
            # Создаем или получаем токен
            token, token_created = Token.objects.get_or_create(user=user)
            
            return Response({
                "auth": True, 
                "token": token.key,
                "user_id": user.id,
                "username": user.username,
                "created": created
            }, status=200)
            
        except Exception as e:
            print(f"Error in TelegramAuthView: {str(e)}")
            return Response({
                "auth": False, 
                "token": "", 
                "error": f"Server error: {str(e)}"
            }, status=500)