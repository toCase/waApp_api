import hmac
import hashlib
import json
from datetime import date
from calendar import monthrange

from django.conf import settings
from django.db.models import Q, Count
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.models import User

from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated, AllowAny

from urllib.parse import parse_qsl, unquote
from .models import *
from .serializer import *

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
                
            print(f"User data: {user_data_str}")
            
            telegram_id = user_data.get("id")
            username = user_data.get("username", "")
            first_name = user_data.get("first_name", username)
            last_name = user_data.get("last_name", "")
            
            if not telegram_id:
                return Response({
                    "auth": False, 
                    "token": "", 
                    "error": "telegram id is missing"
                }, status=400)
            
            # Создаем или получаем пользователя
            user, created = User.objects.get_or_create(
                username=f"{telegram_id}_{username}",
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
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
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff,
                "is_admin": user.is_superuser
            }, status=200)
            
        except Exception as e:
            print(f"Error in TelegramAuthView: {str(e)}")
            return Response({
                "auth": False, 
                "token": "", 
                "error": f"Server error: {str(e)}"
            }, status=500)
            
class TokenAuthView(APIView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        user = request.user
        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "auth": True,
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
            "first_name": user.username,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_admin": user.is_superuser
        }, status=200)

class StaffApiList(generics.ListCreateAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        user = serializer.validated_data.get('user')
        if user and not user.is_staff:
            user.is_staff = True
            user.save()
        serializer.save(user=user)

class StaffApiUpdate(generics.UpdateAPIView):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

class UserApiList(generics.ListAPIView):
    queryset = User.objects.filter(Q(is_staff=False) & Q(is_superuser=False))
    serializer_class = UserSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

class ScheduleApiList(generics.ListCreateAPIView):
    serializer_class = ScheduleSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return ScheduleTemplate.objects.annotate(intervals_count=Count("intervals"));

class ScheduleApiUpdate(generics.UpdateAPIView):
    queryset = ScheduleTemplate.objects.all()
    serializer_class = ScheduleSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)



class IntervalsApiList(generics.ListCreateAPIView):
    queryset = TemplateInterval.objects.all()
    serializer_class = IntervalSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        schedule_id = self.kwargs['schedule_id']
        return TemplateInterval.objects.filter(Q(schedule_id=schedule_id))

    def perform_create(self, serializer):
        schedule_id = self.kwargs['schedule_id']
        serializer.save(schedule_id=schedule_id)

class IntervalsRemove(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def delete(self, request, schedule_id):
        deleted, _ = TemplateInterval.objects.filter(Q(schedule_id=schedule_id)).delete()
        return Response({'deleted': deleted}, status=status.HTTP_204_NO_CONTENT)

class ScheduleCalendar(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        year = int(request.query_params.get("year", date.today().year))
        month = int(request.query_params.get("month", date.today().month))
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])

        slots = (WorkSlot.objects.filter(work_day__range=(start_date, end_date))
                 .select_related('staff')
                 .order_by('staff_id', 'work_day')
                 .values('staff_id', 'staff__title', 'work_day')
                 .distinct())
        data = {}
        for slot in slots:
            sid = slot['staff_id']
            if sid not in data:
                data[sid] = {
                    'staff' : {
                        'id':sid,
                        'title': slot['staff__title'],
                    },
                    'days':[],
                }
            data[sid]['days'].append(slot['work_day'].day)

        result = list(data.values())
        serializer = StaffScheduleSerializer(result, many=True)
        return Response(serializer.data)
