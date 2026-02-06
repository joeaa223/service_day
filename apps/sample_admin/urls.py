from django.urls import path
from . import views

urlpatterns = [
    path("sample_admin/", views.sample_admin_page, name="sample_admin"),
]
