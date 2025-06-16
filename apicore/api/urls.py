from django.urls import path, include, re_path
from . import views

urlpatterns = [
    path('v1/post_list', views.PostApiList.as_view(), name='posts_list'),
    path('v1/post/<int:pk>', views.PostApiUpdate.as_view(), name='post_update'),
    path('v1/category_list', views.CategoryApiList.as_view(), name='category_lis'),
    path('v1/category/<int:pk>', views.CategoryApiUpdate.as_view(), name='category_update'),
    path('v1/auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.authtoken')),
    path('auth/telegram', views.TelegramAuthView.as_view(), name="telegram_auth"),
    path('auth/user', )

]