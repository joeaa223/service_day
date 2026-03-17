from django.urls import path
from . import views


urlpatterns = [
    path("", views.notification_list, name="notification_list"), 
    path("<int:notif_id>/read/", views.notification_mark_read, name="notification_mark_read"),
    path("read-all/", views.notification_mark_all_read, name="notification_mark_all_read"),
    path("manage/", views.manage, name="notification_manage"),
    path("reminder/create/", views.admin_notification_reminder_create, name="admin_notification_reminder_create"),
    path("send-custom/", views.admin_notification_send_custom, name="admin_notification_send_custom"),
]
