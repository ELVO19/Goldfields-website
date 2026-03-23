from django.contrib import admin

# Register your models here.
from restaurant.models import *

admin.site.register(Dish)
admin.site.register(Payment)
admin.site.register(Reservation)
