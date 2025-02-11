from django.db import models
from django.contrib.auth.models import AbstractUser



class Account(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length = 250, blank=True)
    fullname = models.CharField(max_length=500)


    REQUIRED_FIELDS = ['username', "password"]
    USERNAME_FIELD = "email"

    def __str__(self):
        return f"{self.email}"


class Token(models.Model):
    access_token = models.TextField()
    refresh_token = models.TextField()
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_blacklisted = models.BooleanField(default=False)
    blacklisted_at = models.DateTimeField(auto_now=True)
