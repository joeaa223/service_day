from django.contrib import admin
from .models import NGO, Activity

@admin.register(NGO)
class NGOAdmin(admin.ModelAdmin):
    list_display = ('name',) # 刚才你只写了 name 和 description，所以这里只放 name

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ('title', 'ngo', 'date', 'current_slots_taken', 'max_slots')
    list_filter = ('ngo', 'date')