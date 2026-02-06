from django.contrib.auth.models import User
from .models import Notification

def notify_all_users(title, message, url):
    users = User.objects.all()

    notifications = [
        Notification(
            user=user,
            title=title,
            message=message,
            url=url
        )
        for user in users
    ]

    Notification.objects.bulk_create(notifications)
