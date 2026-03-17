import base64
from io import BytesIO

import qrcode

from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse

from apps.activities.models import Activity, Participation

@login_required
def scanner(request):
    return render(request, "checkin/scanner.html")
    
@login_required
def user_checkin(request, acty_id):
    activity = get_object_or_404(Activity, id=acty_id)

    participation = Participation.objects.filter(
        user=request.user,
        acty=activity,
        status="joined"
    ).first()

    if not participation:
        messages.error(request, "You are not registered for this activity.")
        return redirect("dashboard")

    if participation.status == "checked_in":
        messages.info(request, "You have already checked in.")
        return redirect("activity_manage", acty_id=activity.id)

    participation.check_in_on = timezone.now()
    participation.status = "checked_in"
    participation.save(update_fields=["check_in_on","status"])

    messages.success(request, f"Check-in successful for {activity.title}.")
    return redirect("activity_manage", acty_id=activity.id)

def display(request, acty_id):
    activity = get_object_or_404(Activity, id=acty_id)

    checkin_url = request.build_absolute_uri(
        reverse("user_checkin", kwargs={"acty_id": activity.id})
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=12,
        border=4,
    )
    qr.add_data(checkin_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    joined_count = activity.participations.filter(status="joined").count()
    checked_in_count = activity.participations.filter(status="checked_in").count()

    context = {
        "activity": activity,
        "checkin_url": checkin_url,
        "qr_base64": qr_base64,
        "joined_count": joined_count,
        "checked_in_count": checked_in_count,
        "max_participants": getattr(activity, "max_participants", None),
        "remaining_slots": (
            activity.max_participants - joined_count
            if getattr(activity, "max_participants", None) is not None
            else None
        ),
        "display_pin": "1234",  # optional
    }

    return render(request, "checkin/display.html", context)