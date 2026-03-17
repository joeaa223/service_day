from django.contrib import messages
from django.contrib.auth.decorators import login_required,user_passes_test
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.ngo.models import NGO
from apps.notifications.services import notify_activity, notify_activity_staff


from .models import Activity, Participation

def is_admin(user):
    return user.is_staff

@login_required
def activity_manage(request, acty_id):
    activity = get_object_or_404(
        Activity,
        id=acty_id
    )
    if activity.status == "deleted":
        raise Http404("Activity not found")
    
    if request.method == "POST":
        action = request.POST.get("action")

        if action == "update_activity" and request.user.is_staff:
            activity.title = request.POST.get("title", "").strip()
            activity.description = request.POST.get("description", "").strip()
            activity.service_type = request.POST.get("service_type", "").strip()
            activity.address = request.POST.get("address", "").strip()
            activity.postcode = request.POST.get("postcode", "").strip()
            activity.city = request.POST.get("city", "").strip()
            activity.state = request.POST.get("state", "").strip()
            activity.status = request.POST.get("status", "draft").strip()

            max_capacity = request.POST.get("max_capacity")
            if max_capacity:
                activity.max_capacity = max_capacity

            activity_datetime = request.POST.get("activity_datetime")
            cutoff_datetime = request.POST.get("cutoff_datetime")

            if activity_datetime:
                parsed_activity_datetime = parse_datetime(activity_datetime)
                if parsed_activity_datetime:
                    activity.activity_datetime = parsed_activity_datetime

            if cutoff_datetime:
                parsed_cutoff_datetime = parse_datetime(cutoff_datetime)
                if parsed_cutoff_datetime:
                    activity.cutoff_datetime = parsed_cutoff_datetime

            activity.save()

            return redirect("activity_manage", acty_id=activity.id)

    participant_count = Participation.objects.filter(
    acty=activity,
    status__in=["joined", "checked_in"]
).count()

    user_participation = Participation.objects.filter(
        acty=activity,
        user=request.user
    ).first()

    context = {
        "activity": activity,
        "participant_count": participant_count,
        "user_participation": user_participation,
        "now": timezone.now(),
        "remaining_slots": max(activity.max_capacity - participant_count, 0),
        "participations": activity.participations.select_related("user").order_by("-created_on")
    }

    return render(request, "activities/manage.html", context)
    
@login_required
def activity_listing(request):
    now = timezone.now()

    if request.user.is_staff:
        activities = (
            Activity.objects
            .exclude(status="delete")
            .select_related("org")
            .order_by("-activity_datetime")
        )
    else:
        activities = (
            Activity.objects
            .filter(
                Q(status="active") |
                Q(participations__user=request.user, participations__status="joined")
            )
            .filter(activity_datetime__gte=now)
            .select_related("org")
            .distinct()
            .order_by("-activity_datetime")
        )

    context = {
        "activities": activities
    }

    return render(request, "activities/listing.html", context)


@user_passes_test(is_admin)
def create(request):
    ngos = NGO.objects.filter(is_active=True).order_by("name")

    if request.method == "POST":
        org_id = request.POST.get("org")
        title = request.POST.get("title")
        description = request.POST.get("description")
        service_type = request.POST.get("service_type")
        activity_datetime = parse_datetime(request.POST.get("activity_datetime"))
        cutoff_datetime = parse_datetime(request.POST.get("cutoff_datetime"))
        address = request.POST.get("address")
        postcode = request.POST.get("postcode")
        city = request.POST.get("city")
        state = request.POST.get("state")
        max_capacity = request.POST.get("max_capacity")
        
        org = NGO.objects.get(id=org_id)

        activity = Activity.objects.create(
            org=org,
            title=title,
            description=description,
            service_type=service_type,
            activity_datetime=activity_datetime,
            cutoff_datetime=cutoff_datetime,
            address=address,
            postcode=postcode,
            city=city,
            state=state,
            max_capacity=max_capacity,
            created_by=request.user,
        )

        return redirect("activity_manage", acty_id=activity.id)

    return render(request, "activities/create.html", {
        "ngos": ngos,
    })

@user_passes_test(is_admin)
def activity_delete(request, acty_id):
    activity = get_object_or_404(Activity, id=acty_id)

    if request.method == "POST":
        activity.status = "deleted"
        activity.deleted_on = timezone.now()
        activity.save(update_fields=["deleted_on","status"])

        messages.success(request, "Activity deleted successfully.")

    return redirect("activity_listing")

@login_required
def participate(request, acty_id):
    if request.method != "POST":
        return redirect("activity_manage", acty_id=acty_id)

    activity = get_object_or_404(
        Activity,
        id=acty_id,
        deleted_on__isnull=True
    )

    action = request.POST.get("action")

    participation = Participation.objects.filter(
        user=request.user,
        acty=activity
    ).first()

    if action == "join_activity":
        if participation:
            participation.status = "joined"
            participation.cancelled_on = None
            participation.cancelled_by = None
            participation.save()
        else:
            Participation.objects.create(
                user=request.user,
                acty=activity,
                created_by=request.user,
                status="joined"
            )

    elif action == "withdraw_activity" and participation:
        participation.status = "cancelled"
        participation.cancelled_on = timezone.now()
        participation.cancelled_by = request.user
        participation.save()

     # 1. Notify the joining user
    notify_activity(
        user=request.user,
        activity=activity,
        action="joined",
        actor=request.user,
    )

    # 2. Notify activity-related staff/admins
    notify_activity_staff(
        activity=activity,
        title="New Activity Registration",
        message=f"{request.user.get_full_name() or request.user.username} joined '{activity.title}'.",
        event_type="activity_participant_joined",
        extra_data={
            "participant_id": request.user.id,
            "participant_name": request.user.get_full_name() or request.user.username,
            "action": "joined",
        },
        exclude_user_ids=[request.user.id],  # avoid duplicate to joining user
    )

    return redirect("activity_manage", acty_id=activity.id)