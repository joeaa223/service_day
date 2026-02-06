from django.contrib.auth.models import User
from .models import Notification


def notify_user(user, title, message, url):
    """
    Send notification to a single user
    """
    Notification.objects.create(
        user=user,
        title=title,
        message=message,
        url=url
    )

def notify_users(users, title, message, url):
    """
    Send notification to a list/queryset of users
    """
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


def notify_all_users(title, message, url):
    """
    Broadcast notification to all users
    """
    users = User.objects.all()
    notify_users(users, title, message, url)
