from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

def is_admin(user):
    return user.is_staff

@user_passes_test(is_admin)
def sample_admin_page(request):
    return render(request, "sample_admin/page.html")
