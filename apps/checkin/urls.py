from django.urls import path
from . import views

urlpatterns = [
    path("scanner", views.scanner, name="scanner"),
    path("checkin/<uuid:acty_id>/", views.user_checkin, name="user_checkin"),
    path("checkin/display/<uuid:acty_id>/", views.display, name="display"),
]


