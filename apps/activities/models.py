from django.db import models
from django.utils import timezone

#MGO model
class NGO(models.Model):
    name = models.CharField(max_length=255) #NGO name
    description = models.TextField(blank=True) #NGO description

    def __str__(self):
        return self.name


#Activity model
class Activity(models.Model):
    #connect to NGO model, if NGO is deleted, delete all activities also delete
    ngo = models.ForeignKey(NGO, on_delete=models.CASCADE,related_name='activities')
    title = models.CharField(max_length=255) #Activity title
    date = models.DateTimeField() #Activity date
    location = models.CharField(max_length=255) #Activity location
    max_slots = models.IntegerField() #Activity max slots
    current_slots_taken = models.IntegerField(default=0) #Activity current slots taken
    registration_deadline = models.DateTimeField() #Activity registration deadline

    def __str__(self):
        return self.title

    #Check if activity is full
    @property
    def is_full(self):
        return self.current_slots_taken >= self.max_slots
    
    #Check if activity is past deadline
    @property
    def is_past_deadline(self):
        return timezone.now() > self.registration_deadline
    