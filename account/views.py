from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Account
import logging
from django.http import HttpResponseRedirect
from .perms import CustomValidationException, IsAuthenticatedAndNotBlacklisted
from employee.perms import IsAuthenticatedAndOnboardEmployee
from .models import Token
from rest_framework.permissions import IsAdminUser
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from employee.perms import IsAuthenticatedAndCRUDEmployee
from employee.models import Employee
from .serializers import EmployeeRegistrationSerializer, CustomTokenObtainPairSerializer, CreateGroupSerializer, AddUserToGroupSerializer,EmailValidationSerializer,Validate_Token, PasswordValidationSerializer
from django.core.mail import send_mail
from .tasks import send_password_confirmation_email



logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticatedAndOnboardEmployee])
def register(request):
    try:
        serializer = EmployeeRegistrationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        # print(serializer.EmployeeRegistrationSerializer.send_password_reset_email)
        serializer.save()

        return Response({"success": "Employee added successfully"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        # Log the exception for debugging (consider using a proper logging library)
        logger.error(f"Failed to add user record: {e}")
        return Response({"error": "Failed to add user record"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@permission_classes([AllowAny])
def password_reset_link_confirmation(request, uidb64, token):
    try:
        validation = Validate_Token(request)

        user = validation.validate_token_and_user(uidb64, token)
        email_address = user.email

        return HttpResponseRedirect(f"https://alluvium.net/?email={email_address}&token={token}")

    except Exception as e:
        # Log the exception for debugging (consider using a proper logging library)
        logger.error(f"Error: {e}")
        return Response({"error": f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

@api_view(["GET"])
@permission_classes([IsAuthenticatedAndNotBlacklisted])
def logout(request):
    # blacklist the token to make the token invalid ----> purpose of logout
    access_token = request.META.get("HTTP_AUTHORIZATION", "").split(" ")
    access_token = access_token[1]  # Assuming it's a Bearer token
    token = Token.objects.filter(access_token=access_token).first()
    if not token:
        raise CustomValidationException({"message":"Invalid token"}, 403)
    token.is_blacklisted = True
    token.save()

    return Response({"message": "logged out successfully"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def password_confirmation(request):

    serializer = PasswordValidationSerializer(data = request.data)


    try:
        serializer.is_valid(raise_exception=True)
        email_address = serializer.validated_data['email']
        user = Account.objects.get(email=email_address)

        user.set_password(serializer.validated_data['password'])
        user.save()

        send_password_confirmation_email.delay(user.fullname,user.email)
        return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)

    except Account.DoesNotExist:
        return Response({"message":"User not found"}, status=status.HTTP_400_BAD_REQUEST)
    except CustomValidationException as e:
        error_response = e.to_res()
        if error_response['message'] == "Token has Expired":
            # return Response(error_response['message'], 400)

            return HttpResponseRedirect(f"https://alluvium.net/")

        return Response(error_response['message'], 400)

    except Exception as e:
        logger.error(f"Error: {e}")
        return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([AllowAny])
def click_to_reset_password(request):

    serializer = EmailValidationSerializer(data=request.data, context={'request': request})

    try:
        serializer.is_valid(raise_exception=True)
        return Response({"success": "Password reset link sent successfully!"}, status=status.HTTP_200_OK)

    except CustomValidationException as e:
        return Response(e.to_res(), 400)

@api_view(["POST"])
@permission_classes([IsAdminUser])
def create_group(request):
    serializer = CreateGroupSerializer(data = request.data)
    serializer.is_valid(raise_exception=True)

    group_name = serializer.validated_data["name"]
    new_group, _ = Group.objects.get_or_create(name = group_name)

    model_name = serializer.validated_data["model_name"]
    permissions = serializer.validated_data["permissions"]

    # Get the content type for the specified model
    content_type = ContentType.objects.get(model=model_name.lower())

    # Create permissions if they do not exist
    for permission_codename in permissions:
        permission, perm_created = Permission.objects.get_or_create(
            codename=permission_codename,
            content_type=content_type,
            defaults={"name": f"Can {permission_codename.replace('_', ' ')} {model_name}"}
        )
        new_group.permissions.add(permission)


    return Response({"message": f"Group '{group_name}' created successfully.", "permissions_added": permissions}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def add_user_to_group(request):
    serializer = AddUserToGroupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.validated_data['user']
    group = serializer.validated_data['group']

    # Add user to the group
    group.user_set.add(user)

    return Response({"message": f"User '{user.email}' has been added to group '{group.name}'."})
