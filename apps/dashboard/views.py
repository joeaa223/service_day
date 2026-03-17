from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from apps.notifications.services import notify_all_users # import defined notification service

from django.utils import timezone
from django.db.models import Count, Q

from apps.activities.models import Activity, Participation

def is_admin(user):
    return user.is_staff

@login_required
def dashboard(request):
    now = timezone.now()

    context = {
        "now": now,
    }

    # STAFF DASHBOARD
    if request.user.is_staff:
        total_activities = Activity.objects.filter(
            deleted_on__isnull=True
        ).exclude(
            status="delete"
        ).count()

        upcoming_activities = (
            Activity.objects
            .filter(
                deleted_on__isnull=True,
                status="active",
                activity_datetime__gte=now
            )
            .annotate(
                current_participants=Count(
                    "participations",
                    filter=Q(participations__status="joined")
                )
            )
            .select_related("org")
            .order_by("activity_datetime")[:6]
        )

        upcoming_activities_count = (
            Activity.objects
            .filter(
                deleted_on__isnull=True,
                status="active",
                activity_datetime__gte=now
            )
            .count()
        )

        draft_activities = (
            Activity.objects
            .filter(
                deleted_on__isnull=True,
                status="draft"
            )
            .select_related("org")
            .order_by("-created_on")[:6]
        )

        draft_activities_count = (
            Activity.objects
            .filter(
                deleted_on__isnull=True,
                status="draft"
            )
            .count()
        )

        open_activities_count = (
            Activity.objects
            .filter(
                deleted_on__isnull=True,
                status="active",
                cutoff_datetime__gte=now,
                activity_datetime__gte=now
            )
            .count()
        )

        context.update({
            "total_activities": total_activities,
            "upcoming_activities": upcoming_activities,
            "upcoming_activities_count": upcoming_activities_count,
            "draft_activities": draft_activities,
            "draft_activities_count": draft_activities_count,
            "open_activities_count": open_activities_count,
        })

    # NORMAL USER DASHBOARD
    else:
        joined_count = Participation.objects.filter(
            user=request.user,
            status="joined"
        ).count()

        participated_count = Participation.objects.filter(
            user=request.user,
            status__in=["checked_in", "archived"]
        ).count()

        my_upcoming_participations = (
            Participation.objects
            .select_related("acty", "acty__org")
            .filter(
                user=request.user,
                status="joined",
                acty__deleted_on__isnull=True,
                acty__status="active",
                acty__activity_datetime__gte=now
            )
            .order_by("acty__activity_datetime")[:5]
        )

        upcoming_joined_count = (
            Participation.objects
            .filter(
                user=request.user,
                status="joined",
                acty__deleted_on__isnull=True,
                acty__status="active",
                acty__activity_datetime__gte=now
            )
            .count()
        )

        available_activities = (
            Activity.objects
            .filter(
                deleted_on__isnull=True,
                status="active",
                cutoff_datetime__gte=now,
                activity_datetime__gte=now
            )
            .annotate(
                current_participants=Count(
                    "participations",
                    filter=Q(participations__status="joined")
                )
            )
            .exclude(
                participations__user=request.user,
                participations__status__in=["joined", "checked_in", "archived"]
            )
            .select_related("org")
            .order_by("activity_datetime")[:6]
        )

        available_activities_count = (
            Activity.objects
            .filter(
                deleted_on__isnull=True,
                status="active",
                cutoff_datetime__gte=now,
                activity_datetime__gte=now
            )
            .exclude(
                participations__user=request.user,
                participations__status__in=["joined", "checked_in", "archived"]
            )
            .distinct()
            .count()
        )

        context.update({
            "joined_count": joined_count,
            "participated_count": participated_count,
            "my_upcoming_participations": my_upcoming_participations,
            "upcoming_joined_count": upcoming_joined_count,
            "available_activities": available_activities,
            "available_activities_count": available_activities_count,
        })

    return render(request, "dashboard/index.html", context)

@login_required
def user_dashboard(request):
    return render(request, "dashboard/user.html")

@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, "dashboard/admin.html")

@login_required
@user_passes_test(is_admin)
def broadcast_test(request):
    if request.method == "POST":
        message = request.POST.get("message")

        if message:
            sender_name = (
                request.user.get_full_name()
                if request.user.get_full_name()
                else request.user.username
            )
            
            notify_all_users(
                title=f"Broadcast from {sender_name}",
                message=message,
                url="/notifications/"
            )

        return redirect("broadcast_test")

    return render(request, "dashboard/broadcast_test.html")
