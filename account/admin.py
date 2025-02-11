from django.contrib import admin
from .models import Account

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["fullname", "email", "date_joined", "is_active"]

# Register your models here.
