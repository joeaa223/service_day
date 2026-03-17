from django.conf import settings
from django.db import models
from django.utils import timezone

import uuid
from apps.ngo.models import NGO


class Activity(models.Model): 
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("deleted", "Deleted"),
        ("active", "Active"),
        ("archived", "Archived"),
    ]
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    org = models.ForeignKey(NGO, on_delete=models.CASCADE, related_name="activities")

    title = models.CharField(max_length=200)
    description = models.TextField()
    service_type = models.CharField(max_length=50)

    activity_datetime = models.DateTimeField()
    cutoff_datetime = models.DateTimeField()

    address = models.TextField()
    postcode = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=100,)
    state = models.CharField(max_length=100)
    
    max_capacity = models.PositiveIntegerField()
    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities_created",
    )
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activities_deleted",
    )

    def __str__(self):
        return f"{self.org.name} - {self.title}"

    @property
    def joined_count(self):
        return self.participations.filter(status="joined").count()

    @property
    def available_slots(self):
        return max(self.max_capacity - self.joined_count, 0)

    @property
    def is_open(self):
        return timezone.now() <= self.cutoff_datetime and self.available_slots > 0


class Participation(models.Model):
    STATUS_CHOICES = [
        ("joined", "Joined"),
        ("cancelled", "Cancelled"),
        ("absent", "Absent"),
        ("checked_in", "Checked-in"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="participations",
    )
    acty = models.ForeignKey(
        Activity,
        on_delete=models.CASCADE,
        related_name="participations",
    )

    created_on = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="participations_created",
    )
    cancelled_on = models.DateTimeField(null=True, blank=True)
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="participations_cancelled",
    )
    check_in_on = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="joined")

    class Meta:
        unique_together = ("user", "acty")

    def __str__(self):
        return f"{self.user} - {self.acty}"