from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse

from django.core.mail import send_mail

def generate_password_reset_email(user, request):
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    reset_url = request.build_absolute_uri(
        reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    )
    return reset_url


def send_password_reset_email(fullname , email, reset_url):
        subject = "Set Your Password"
        message = f"Hi {fullname},\n\nPlease set your password by clicking the link below:\n{reset_url}\n\nThank you!"
        recipient_list = [email]
        send_mail(subject, message, None, recipient_list, fail_silently=False)


def send_reset_account_password(request, existing_account):
        # Generate the password reset URL and send it
        reset_url = generate_password_reset_email(existing_account, request)

        # send password reset email to user
        send_password_reset_email(existing_account.fullname, existing_account.email, reset_url)