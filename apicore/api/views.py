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
from decouple import config
from django.contrib.auth import get_user_model
from .models import *
from .serializer import *

BOT_TOKEN = config('TG_BOT_TOKEN')
User = get_user_model()

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

class TelegramAuthView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        init_data = request.data.get("initData", "")
        if not init_data:
            return Response({"auth": False, "token": ""}, status=400)

        data_dict = dict(parse_qsl(init_data, keep_blank_values=True))
        hash_from_telegram = data_dict.pop("hash", None)

        check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
        secret_key = hashlib.sha256(BOT_TOKEN.encode()).digest()
        hmac_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

        if hmac_hash != hash_from_telegram:
            return Response({"auth": False, "token": ""}, status=403)

        try:
            user_id = data_dict.get("user", "")
            user_data = eval(user_id) if isinstance(user_id, str) else user_id
            telegram_id = user_data["id"]
            username = user_data.get("username", f"user_{telegram_id}")
        except Exception:
            return Response({"auth": False, "token": ""}, status=400)

        user, _ = User.objects.get_or_create(username=str(telegram_id), defaults={"first_name": username})
        token, _ = Token.objects.get_or_create(user=user)

        return Response({"auth": True, "token": token.key})