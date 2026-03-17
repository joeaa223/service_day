from django.contrib.auth.models import User
from django.db import transaction

from .models import Notification
from apps.activities.models import Participation
from apps.websocket.services import websocket_push


def build_notification_payload(notification, unread_count=None, extra_data=None):
    return {
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "url": notification.url,
        "is_read": notification.is_read,
        "created_on": notification.created_on.isoformat() if hasattr(notification, "created_on") and notification.created_on else None,
        **(extra_data or {}),
    }


def push_notification_event(user, notification, event_type="notification", extra_data=None):
    unread_count = Notification.objects.filter(user=user, is_read=False).count()

    websocket_push(
        user_id=user.id,
        event_type=event_type,
        message=notification.message,
        count=unread_count,
        data=build_notification_payload(
            notification=notification,
            unread_count=unread_count,
            extra_data=extra_data,
        ),
    )


def notify_user(
    user,
    title,
    message,
    url=None,
    event_type="notification",
    extra_data=None,
):
    """
    Create notification in DB, then push websocket event.
    """
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        url=url,
    )

    push_notification_event(
        user=user,
        notification=notification,
        event_type=event_type,
        extra_data=extra_data,
    )

    return notification


def notify_users(
    users,
    title,
    message,
    url=None,
    event_type="notification",
    extra_data=None,
):
    """
    Save notification for many users, then push individually.
    """
    created_notifications = []

    with transaction.atomic():
        for user in users:
            notification = Notification.objects.create(
                user=user,
                title=title,
                message=message,
                url=url,
            )
            created_notifications.append((user, notification))

    for user, notification in created_notifications:
        push_notification_event(
            user=user,
            notification=notification,
            event_type=event_type,
            extra_data=extra_data,
        )

    return [n for _, n in created_notifications]


def notify_all_users(title, message, url=None, event_type="notification", extra_data=None):
    users = User.objects.all()
    return notify_users(
        users=users,
        title=title,
        message=message,
        url=url,
        event_type=event_type,
        extra_data=extra_data,
    )

def notify_activity(user, activity, action, actor=None):
    """
    Notification helper for activity-related events.

    action examples:
        joined
        cancelled
        updated
        checked_in
        reminder
    """
    activity_url = f"/activities/{activity.id}/"

    if action == "joined":
        title = "Activity Joined"
        message = f"You have successfully joined '{activity.title}'."
        event_type = "activity_joined"

    elif action == "cancelled":
        title = "Activity Cancelled"
        message = f"Your participation for '{activity.title}' has been cancelled."
        event_type = "activity_cancelled"

    elif action == "updated":
        title = "Activity Updated"
        message = f"'{activity.title}' has been updated."
        event_type = "activity_updated"

    elif action == "checked_in":
        title = "Check-In Successful"
        message = f"You have successfully checked in to '{activity.title}'."
        event_type = "activity_checked_in"

    elif action == "reminder":
        title = "Activity Reminder"
        message = f"Reminder: '{activity.title}' is happening soon."
        event_type = "activity_reminder"

    else:
        title = "Activity Notification"
        message = f"There is an update for '{activity.title}'."
        event_type = "activity_notification"

    return notify_user(
        user=user,
        title=title,
        message=message,
        url=activity_url,
        event_type=event_type,
        extra_data={
            "activity_id": activity.id,
            "activity_title": activity.title,
            "action": action,
            "actor_id": actor.id if actor else None,
            "actor_name": actor.get_full_name() if actor else None,
        },
    )

def get_activity_related_users(activity, exclude_user_ids=None):

    exclude_user_ids = exclude_user_ids or []

    related_users = []

    # Staff
    related_users.append(activity.created_by)

     # Participants from Participation table
    participations = Participation.objects.select_related("user").filter(acty=activity)

    for p in participations:
        related_users.append(p.user)

    # remove duplicates + excluded users
    unique_users = {}
    for user in related_users:
        if user and user.id not in exclude_user_ids:
            unique_users[user.id] = user

    return list(unique_users.values())


def notify_activity_staff(activity, title, message, event_type, extra_data=None, exclude_user_ids=None):

    exclude_user_ids = exclude_user_ids or []

    users = get_activity_related_users(
        activity,
        exclude_user_ids=exclude_user_ids
    )

    return notify_users(
        users=users,
        title=title,
        message=message,
        url=f"/activities/{activity.id}/",
        event_type=event_type,
        extra_data={
            "activity_id": activity.id,
            "activity_title": activity.title,
            **(extra_data or {}),
        },
    )