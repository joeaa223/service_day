from django.urls import path
from . import views

urlpatterns = [
    path("ngo/", views.listing, name="ngo_listing"),
    path("ngo/register/", views.register, name="register_ngo"),
    path("ngo/<uuid:ngo_id>/", views.manage, name="manage_ngo"),
]
