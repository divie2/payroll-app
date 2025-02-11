from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from celery import shared_task
from .models import Account

from rest_framework import status
from rest_framework.response import Response


from django.core.mail import send_mail

def generate_password_reset_email(domain, user):
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    full_reset_url = f"{domain}/{reset_url}"

    print(full_reset_url)

    return full_reset_url


def send_password_reset_email(fullname , email, reset_url):
        subject = "Set Your Password"
        message = f"Hi {fullname},\n\nPlease set your password by clicking the link below:\n{reset_url}\n\nThank you!"
        recipient_list = [email]
        send_mail(subject, message, None, recipient_list, fail_silently=False)

@shared_task
def send_reset_account_password(domain, existing_account):

        existing_account = Account.objects.get(pk=existing_account)

        print(f"{existing_account} existing account")

        # Generate the password reset URL and send it
        reset_url = generate_password_reset_email(domain, existing_account)

        # send password reset email to user

        send_password_reset_email(existing_account.fullname, existing_account.email, reset_url)

@shared_task
def send_password_confirmation_email(fullname, email):

        subject = "Password Reset Successful"
        message = f"Hi {fullname} your password have been reset!"
        recipient_list = [email]

        send_mail(subject, message, None, recipient_list, fail_silently=False)

        