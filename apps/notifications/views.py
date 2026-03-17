from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.utils import timezone

from datetime import timedelta
from django.contrib import messages

from .models import Notification
from apps.activities.models import Activity,Participation
from apps.websocket.services import websocket_push
from .services import notify_user, notify_users



def is_admin(user):
    return user.is_staff

@login_required
def notification_list(request):
    notifications = (
        Notification.objects
        .filter(user=request.user)
        .order_by("-created_at")
    )

    unread_count = notifications.filter(is_read=False).count()

    context = {
        "notifications": notifications,
        "unread_count": unread_count,
    }
    return render(request, "notifications/list.html", context)


@login_required
@require_POST
def notification_mark_read(request, notif_id):
    notification = get_object_or_404(
        Notification,
        id=notif_id,
        user=request.user,
    )

    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=["is_read"])

    if notification.url:
        return redirect(notification.url)

    return redirect("notification_list")


@login_required
@require_POST
def notification_mark_all_read(request):
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return redirect("notification_list")

@user_passes_test(is_admin)
def manage(request):
    now = timezone.now()

    activities = (
        Activity.objects
        .filter(deleted_on__isnull=True)
        .order_by("activity_datetime")
    )

    # If you already have a reminder model, replace this with real query
    reminders = []
    # reminders = (
    #     ActivityReminder.objects
    #     .select_related("activity")
    #     .order_by("scheduled_for")[:5]
    # )

    sent_notifications = (
        Notification.objects
        .select_related("user")
        .order_by("created_at")#[:8]
    )

    sent_today_count = Notification.objects.filter(
        created_at__date=now.date()
    ).count()

    unread_admin_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    context = {
        "activities": activities,
        "reminders": reminders,
        "sent_notifications": sent_notifications,
        "reminder_count": len(reminders) if isinstance(reminders, list) else reminders.count(),
        "sent_today_count": sent_today_count,
        "unread_admin_count": unread_admin_count,
    }

    return render(request, "notifications/manage.html", context)

@user_passes_test(is_admin)
def admin_notification_reminder_create(request):
    """
    Creates a reminder configuration payload.
    For now this version validates input and shows success feedback.
    If you already have a Reminder model, save it there.
    """
    activity_id = request.POST.get("activity_id")
    audience = request.POST.get("audience")
    reminder_type = request.POST.get("reminder_type")
    delivery_mode = request.POST.get("delivery_mode")
    offset_value = request.POST.get("offset_value")
    offset_unit = request.POST.get("offset_unit")
    scheduled_for_raw = request.POST.get("scheduled_for")
    title = request.POST.get("title")
    message = request.POST.get("message")

    if not activity_id or not title or not message:
        messages.error(request, "Activity, title, and message are required.")
        return redirect("notification_manage")

    activity = get_object_or_404(Activity, id=activity_id)

    scheduled_for = None

    try:
        if reminder_type == "custom_time" and scheduled_for_raw:
            scheduled_for = timezone.datetime.fromisoformat(scheduled_for_raw)
            if timezone.is_naive(scheduled_for):
                scheduled_for = timezone.make_aware(scheduled_for, timezone.get_current_timezone())
        else:
            value = int(offset_value or 0)

            if reminder_type == "before_start":
                base_dt = getattr(activity, "start_date", None) or getattr(activity, "activity_datetime", None)
            elif reminder_type == "registration_closing":
                base_dt = getattr(activity, "cutoff_datetime", None)
            else:
                base_dt = None

            if not base_dt:
                messages.error(request, "Unable to determine reminder time for this activity.")
                return redirect("notification_manage")

            if offset_unit == "minutes":
                scheduled_for = base_dt - timedelta(minutes=value)
            elif offset_unit == "hours":
                scheduled_for = base_dt - timedelta(hours=value)
            elif offset_unit == "days":
                scheduled_for = base_dt - timedelta(days=value)
            else:
                messages.error(request, "Invalid offset unit.")
                return redirect("notification_manage")
    except ValueError:
        messages.error(request, "Invalid reminder values.")
        return redirect("notification_manage")

    # Replace this section with actual Reminder model save if you have one
    # Example:
    # ActivityReminder.objects.create(
    #     activity=activity,
    #     audience=audience,
    #     reminder_type=reminder_type,
    #     delivery_mode=delivery_mode,
    #     scheduled_for=scheduled_for,
    #     title=title,
    #     message=message,
    #     created_by=request.user,
    #     status="pending",
    # )

    messages.success(
        request,
        f"Reminder scheduled for '{activity.title}' at {timezone.localtime(scheduled_for).strftime('%d %b %Y, %I:%M %p')}."
    )
    return redirect("notification_manage")


@user_passes_test(is_admin)
@require_POST
def admin_notification_send_custom(request):
    target_scope = request.POST.get("target_scope")
    activity_id = request.POST.get("activity_id")
    event_type = request.POST.get("event_type", "notification").strip()
    title = request.POST.get("title")
    message = request.POST.get("message")
    url = request.POST.get("url","")
    delivery_mode = request.POST.get("delivery_mode")

    if not title or not message:
        messages.error(request, "Title and message are required.")
        return redirect("notification_manage")

    activity = None
    if activity_id:
        activity = get_object_or_404(Activity, id=activity_id)

    users = []

    if target_scope == "all_users":
        from django.contrib.auth.models import User
        users = list(User.objects.filter(is_active=True))

    elif target_scope in ["activity_participants", "activity_staff"]:
        if not activity:
            messages.error(request, "Activity is required for this target scope.")
            return redirect("notification_manage")
        users = get_activity_target_users(activity, target_scope)

    elif target_scope == "selected_users":
        # Placeholder for future selected user feature
        messages.error(request, "Selected users target is not implemented yet.")
        return redirect("notification_manage")

    else:
        messages.error(request, "Invalid target scope.")
        return redirect("notification_manage")

    if not users:
        messages.warning(request, "No users found for the selected target.")
        return redirect("notification_manage")

    sent_count = 0

    for user in users:
        payload_data = {
            "title": title,
            "activity_id": activity.id if activity else None,
            "activity_title": activity.title if activity else None,
            "target_scope": target_scope,
            "sent_by": request.user.id,
        }

        if delivery_mode == "both":
            notify_user(
                user=user,
                title=title,
                message=message,
                url=url or (f"/activities/{activity.id}/" if activity else ""),
                event_type=event_type,
                extra_data=payload_data,
            )
            unread_count = Notification.objects.filter(user=user, is_read=False).count()
            websocket_push(
                user_id=user.id,
                event_type=event_type,
                message=message,
                count=unread_count,
                data=payload_data,
            )
            sent_count += 1

        elif delivery_mode == "notification":
            Notification.objects.create(
                user=user,
                title=title,
                message=message,
                url=url or (f"/activities/{activity.id}/" if activity else ""),
            )
            sent_count += 1

        elif delivery_mode == "websocket":
            unread_count = Notification.objects.filter(user=user, is_read=False).count()
            websocket_push(
                user_id=user.id,
                event_type=event_type,
                message=message,
                count=unread_count,
                data=payload_data,
            )
            sent_count += 1

        else:
            messages.error(request, "Invalid delivery mode.")
            return redirect("notification_manage")

    messages.success(request, f"Custom notification sent to {sent_count} user(s).")
    return redirect("notification_manage")

def get_activity_target_users(activity, target_scope):
    """
    Resolve users based on admin form target scope.
    Adjust this function to match your actual Activity relationships.
    """
    if target_scope == "activity_participants":
        return [
            p.user for p in
            Participation.objects.select_related("user").filter(activity=activity, status="joined")
        ]

    if target_scope == "activity_staff":
        users = []

        if hasattr(activity, "created_by") and activity.created_by:
            users.append(activity.created_by)

        if hasattr(activity, "ngo") and hasattr(activity.ngo, "user") and activity.ngo.user:
            users.append(activity.ngo.user)

        if hasattr(activity, "staffs"):
            users.extend(list(activity.staffs.all()))

        if hasattr(activity, "admins"):
            users.extend(list(activity.admins.all()))

        unique = {}
        for user in users:
            if user:
                unique[user.id] = user
        return list(unique.values())

    return []