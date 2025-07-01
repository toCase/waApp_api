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
    path('v1/schedule_template_list', views.ScheduleApiList.as_view(), name="schedule_template_list"),
    path('v1/schedule_template/<int:pk>', views.ScheduleApiUpdate.as_view(), name="schedule_template_update"),
    path('v1/schedule_template/<int:schedule_id>/intervals', views.IntervalsApiList.as_view(), name="template_intervals"),
    path('v1/template_intervals/<int:schedule_id>/delete', views.IntervalsRemove.as_view(), name="delete_intervals"),
    path('v1/staff_schedule/', views.ScheduleCalendar.as_view(), name="schedule_calendar"),
    path('v1/workdays_create', views.WorkslotGenerator.as_view(), name="workdays_create"),
    path('v1/workdays_delete_days', views.WorkslotRemoveDays.as_view(), name="workdays_delete_days"),
    path('v1/workdays_delete/<int:month>/<int:year>/<int:staff_id>', views.WorkslotRemove.as_view(), name="workdays_delete"),
]