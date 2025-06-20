from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('v1/auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('auth/telegram', views.TelegramAuthView.as_view(), name="telegram_auth"),
    path('auth/user', views.TokenAuthView.as_view(), name="token_auth"),
    path('v1/staff_list', views.StaffApiList.as_view(), name="staff_list"),
    path('v1/staff/<int:pk>', views.StaffApiUpdate.as_view(), name="staff_update"),
    path('v1/users_list', views.UserApiList.as_view(), name="users_list"),

]