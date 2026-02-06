from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from apps.notifications.services import notify_all_users # import defined notification service

def is_admin(user):
    return user.is_staff

@login_required
def dashboard(request):
    if request.user.is_staff:
        return redirect("admin_dashboard")
    else:
        return redirect("user_dashboard")
    
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
