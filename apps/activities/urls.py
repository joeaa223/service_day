from django.urls import path
from . import views

urlpatterns = [
    
    path("activities/", views.activity_listing, name="activity_listing"),
    path("activities/create/", views.create, name="create_activity"),
    path("activities/<uuid:acty_id>/", views.activity_manage, name="activity_manage"),
    path("activities/<uuid:acty_id>/participate/", views.participate, name="participate"),
    path("activities/delete/<uuid:acty_id>", views.activity_delete, name="activity_delete"),
]