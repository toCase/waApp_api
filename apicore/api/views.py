import hmac
import hashlib
import json
import math

from datetime import date, datetime, time
from calendar import monthrange
from email.policy import default

from django.conf import settings
from django.db.models import Q, Count, Prefetch
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

            # Get or Create - Client
            client, created = Clients.objects.get_or_create(
                user=user,
                defaults= {
                    'name': f'{first_name} {last_name}',
                    'description': 'TG'
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
                "is_admin": user.is_superuser,
                "client_id": client.id,
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

class LoginAuthView(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        first_name = request.data.get('username')
        email = request.data.get('email')

        if not username or not password:
            return Response({"error": "username and password required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "username already taken"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
        )

        client, _ = Clients.objects.get_or_create(
            user=user,
            defaults={
                'name': first_name,
                'description': ''
            }
        )

        token, _ =Token.objects.get_or_create(user=user)

        return Response({
            "auth": True,
            "token": token.key,
            "user_id": user.id,
            "client_id": client.id,
            "username": user.username,
            "first_name": user.username,
            "last_name": user.last_name,
            "is_staff": user.is_staff,
            "is_admin": user.is_superuser
        }, status=status.HTTP_200_OK)


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

        # Фильтрованные слоты
        slot_qs = WorkSlot.objects.filter(work_day__range=(start_date, end_date))

        # Все активные сотрудники с предзагрузкой только нужных слотов
        staff_qs = Staff.objects.filter(is_active=True).prefetch_related(
            Prefetch('workslot_set', queryset=slot_qs, to_attr='month_slots')
        )

        result = []
        for staff in staff_qs:
            days = [slot.work_day.day for slot in getattr(staff, 'month_slots', [])]
            result.append({
                'staff': staff,
                'days': days
            })

        serializer = StaffScheduleSerializer(result, many=True)
        return Response(serializer.data)

class WorkslotGenerator(APIView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def time_to_minutes(self, t:time):
        return t.hour * 60 + t.minute

    def minutes_to_time(self, minutes:int):
        hour = math.floor(minutes / 60)
        minute = minutes - (hour * 60)
        return time(hour, minute, 00)

    def post(self, request):
        staff_id = request.data.get("staff_id")
        schedule_id = request.data.get("schedule_id")
        days = request.data.get("days", [])

        staff = Staff.objects.get(id=staff_id)
        templates = TemplateInterval.objects.filter(Q(schedule_id=schedule_id))

        # clear old
        try:
            date_list = [datetime.fromisoformat(d).date() for d in days]
        except ValueError as e:
            return Response({"error": f"Invalid date format: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        deleted, _ = WorkSlot.objects.filter(
            staff_id=staff_id,
            work_day__in=date_list
        ).delete()

        #  make new
        created_slots = []

        for day in date_list:
            for template in templates:
                st = self.time_to_minutes(template.start_time)
                ed = self.time_to_minutes(template.end_time)
                slot_size = template.slot_size

                while st < ed:
                    start_time = self.minutes_to_time(st)
                    end_time = self.minutes_to_time(st + slot_size)
                    st += slot_size

                    WorkSlot.objects.create(
                        staff=staff,
                        work_day=day,
                        start_time=start_time,
                        end_time=end_time,
                        is_blocked=False
                    )

                    created_slots.append({
                        "day": day,
                        "start": start_time.strftime("%H: %M"),
                        "end": end_time.strftime("%H:%M")
                    })
        return Response({"created": created_slots}, status=status.HTTP_201_CREATED)

class WorkslotRemoveDays(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        staff_id = request.data.get("staff_id")
        days = request.data.get("days", [])

        try:
            date_list = [datetime.fromisoformat(d).date() for d in days]
        except ValueError as e:
            return Response({"error": f"Invalid date format: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        deleted, _ = WorkSlot.objects.filter(
            staff_id=staff_id,
            work_day__in=date_list
        ).delete()

        return Response({"deleted": deleted}, status=status.HTTP_204_NO_CONTENT)

class WorkslotRemove(APIView):
    authentication_classes = (TokenAuthentication, )
    permission_classes = (IsAuthenticated, )

    def delete(self, request, month:int, year:int, staff_id:int):
        start_date = date(year, month, 1)
        end_date = date(year, month, monthrange(year, month)[1])

        deleted, _ = WorkSlot.objects.filter(Q(work_day__range=(start_date, end_date)) & Q(staff_id=staff_id)).delete()
        return Response({'deleted': deleted}, status=status.HTTP_204_NO_CONTENT)

class WorkdayStaff(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        date_str = request.query_params.get("date")
        if not date_str:
            return Response({"error":"Missing date"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            work_day = date.fromisoformat(date_str)
        except ValueError:
            return Response(data={"error":"Invalid date format"}, status=status.HTTP_400_BAD_REQUEST)

        staff_ids = (WorkSlot.objects.filter(work_day=work_day, staff__isnull=False)
                     .values_list('staff_id', flat=True)
                     .distinct())
        return Response(data={'staff_ids':list(staff_ids)}, status=status.HTTP_200_OK)

class WorkslotAppointemnt(generics.ListAPIView):
    serializer_class = WorkslotListSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        staff_id = self.request.query_params.get("staff")
        work_day = self.request.query_params.get("workday")

        if not staff_id or not work_day:
            return WorkSlot.objects.none()

        queryset = (WorkSlot.objects.filter(Q(staff_id=staff_id) & Q(work_day=work_day))
                    .select_related('appointment','appointment__client')
                    .order_by("start_time"))

        return queryset

    def list(self, request, *args, **kwargs):
        staff_id = request.query_params.get("staff")
        work_day = request.query_params.get("workday")

        if not staff_id:
            return Response(
                {'error': 'staff_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not work_day:
            return Response(
                {'error': 'work_day parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().list(request, *args, **kwargs)

class ClientsList(generics.ListCreateAPIView):
    serializer_class = ClientListSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Clients.objects.annotate(appointment_count=Count('appointment'))

class AppointmentView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        slot_id = request.data.get("slot_id")
        client_id = request.data.get("client_id")
        notes = request.data.get("notes", "")

        if not slot_id:
            return Response({"error":"Missing slot"}, status=status.HTTP_400_BAD_REQUEST)
        if not client_id:
            return Response({"error":"Missing client"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            slot = WorkSlot.objects.get(id=slot_id)
            client = Clients.objects.get(id=client_id)

            if slot.is_blocked:
                return Response({"error":"Slot is blocked"}, status=status.HTTP_400_BAD_REQUEST)

            appointment = Appointment.objects.create(
                slot=slot,
                client=client,
                notes=notes,
                status=0
            )

            # block workslot
            slot.is_blocked = True
            slot.blocked_by = appointment
            slot.save()
            serializer = WorkslotListSerializer(slot)

            return Response(serializer.data, status=status.HTTP_200_OK)


        except WorkSlot.DoesNotExist:
            return Response({"error":"Workslot not found"}, status=status.HTTP_400_BAD_REQUEST)
        except Clients.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        slot_id = request.data.get("slot_id")
        appointment_id = request.data.get("appointment_id")
        client_id = request.data.get("client_id")
        notes = request.data.get("notes", "")
        slot_status = request.data.get("status", 0)

        if not slot_id:
            return Response({"error":"Missing slot"}, status=status.HTTP_400_BAD_REQUEST)
        if not appointment_id:
            return Response({"error":"Missing appointment"}, status=status.HTTP_400_BAD_REQUEST)
        if not client_id:
            return Response({"error":"Missing client"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            slot = WorkSlot.objects.get(id=slot_id)
            client = Clients.objects.get(id=client_id)

            appointment = Appointment.objects.get(id=appointment_id)
            appointment.client = client
            appointment.notes = notes
            appointment.status = slot_status
            appointment.save()

            # block workslot
            serializer = WorkslotListSerializer(slot)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Appointment.DoesNotExist:
            return Response({"error":"Appointment not found"}, status=status.HTTP_400_BAD_REQUEST)
        except WorkSlot.DoesNotExist:
            return Response({"error":"Workslot not found"}, status=status.HTTP_400_BAD_REQUEST)
        except Clients.DoesNotExist:
            return Response({"error": "Client not found"}, status=status.HTTP_400_BAD_REQUEST)