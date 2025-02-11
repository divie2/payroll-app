import re
from employee.models import Employee, Team, NextOfKin, PayrollStaff
from .utills import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_decode
from rest_framework import serializers, exceptions
from .models import Account, Token
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .perms import CustomValidationException
import datetime
from datetime import timezone
from django.contrib.auth.models import Group
from .tasks import send_reset_account_password
from django.core.mail import send_mail



import logging
logger = logging.getLogger("account")

class EmployeeRegistrationSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField()
    team_name = serializers.CharField(required=False)
    nok_name = serializers.CharField(required=False)
    nok_address = serializers.CharField(required=False)
    nok_phone = serializers.CharField(required=False)
    email = serializers.EmailField()
    class Meta:
        model = Employee
        fields = ["jira_ticket_id", "jira_employee_id", "base_pay", "pay_deno", "acct_num", "acct_name", "bank_name", "team_name", "job_role", "job_type", "phone", "start_date", "dob", "id_type", "fullname", "email", "address", "nok_name", "nok_address", "nok_phone"]


    def create_update_account(self, email, fullname):
        request = self.context.get('request')
        existing_account = Account.objects.filter(email = email).first()


        domain = f"{request.scheme}://{request.META.get('HTTP_HOST')}"

        if not existing_account:
            existing_account, _ = Account.objects.get_or_create(fullname=fullname, email = email)

            send_reset_account_password.delay(domain , existing_account.id)
        else:
            if not existing_account.password:

                send_reset_account_password.delay(domain, existing_account.id)

            existing_account.fullname = fullname
            existing_account.save()
        return existing_account


    def create_new_team(self, team_name):
        new_team, _ = Team.objects.get_or_create(name = team_name)
        return new_team

    def create_update_nok(self, existing_employee, nok_name, nok_address, nok_phone):
        existing_nok = NextOfKin.objects.filter(employee = existing_employee).first()
        if not existing_nok:
            if nok_name and nok_address and nok_phone:
                NextOfKin.objects.create(name=nok_name, address=nok_address, phone=nok_phone, employee=existing_employee)
        else:
            if nok_name:
                existing_nok.name = nok_name
            if nok_address:
                existing_nok.address = nok_address
            if nok_phone:
                existing_nok.phone = nok_phone
            existing_nok.save()

        return existing_nok

    def create(self, validated_value):
        # create account for the user here
        existing_account = self.create_update_account(validated_value.get("email"), validated_value.get("fullname"))

        # create new team if team name got sent
        new_team = self.create_new_team(validated_value.get("team_name", "General"))


        nok_name = validated_value.get("nok_name")
        nok_address = validated_value.get("nok_address")
        nok_phone = validated_value.get("nok_phone")

        # remove the email, fullname, password from the serializer
        to_be_removed_fields = ["email", "fullname", "nok_name", "nok_address", "nok_phone", "team_name"]
        for field in to_be_removed_fields:
            if validated_value.get(field):
                validated_value.pop(field)


        # create / update the employee
        existing_employee = Employee.objects.filter(account = existing_account).first()
        if not existing_employee:
            # create new employee
            existing_employee = Employee.objects.create(**validated_value, account=existing_account)

            # add employee to the new team as a member
            new_team.members.add(existing_employee)
            new_team.save()
        else:
            # update employee
            for field_name, field_value in validated_value.items():
                setattr(existing_employee, field_name, field_value)
            existing_employee.save()

        # create next of kin details
        self.create_update_nok(existing_employee, nok_name, nok_address, nok_phone)


        return existing_employee


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def update_old_tokens(self, data):
        # blacklist previous tokens from db and blacklist
        prev_gen_tokens = Token.objects.filter(user=self.user)
        if prev_gen_tokens.exists():
            #  blacklist all token found
            prev_gen_tokens.update(is_blacklisted=True)
        #  to remove existing blacklisted commands that have been created in the last 7 days: Run the delete_blacklisted_tokens command ------> python manage.py delete_blacklisted_tokens
        # add new token to db
        Token.objects.create(
            refresh_token=data["refresh"],
            access_token=data["access"],
            user=self.user,
        )

    def check_active_employee(self):
        if self.user.account:
            if self.user.account.status != "active":
                raise CustomValidationException({"message":"Account disable, please reach out to admin"}, 401)

    def validate(self, attrs):
        try:
            data = super().validate(attrs)
            if not self.user.is_active:
                raise CustomValidationException({"message":"Account disable, please reach out to admin"}, 401)
            if not self.user.is_superuser:
                self.check_active_employee()
            data['uid'] = self.user.id
            data["fullname"] = self.user.fullname
            data['email'] = self.user.email
            # data['permissions'] = self.user.get_all_permissions()
            data['is_payroll_staff'] = PayrollStaff.objects.filter(employee__account=self.user).exists()


            self.update_old_tokens(data)

            self.user.last_login = datetime.datetime.now(timezone.utc)

            # data['open_stack_token'] = open_stack_token
            self.user.save()

        except (exceptions.AuthenticationFailed, exceptions.NotAuthenticated) as e:
            logger.warning(f"Failed login attempt for user: {attrs.get('email')} {e}")
            # check if user is active
            corres_user = Account.objects.filter(email=attrs.get('email'))
            if corres_user.exists():
                if not corres_user.first().is_active:
                    raise CustomValidationException({"message":"Account disable, please reach out to admin"}, 401)
            # res_data = {"statuscode":"01", "statusmessage":"Failed"}
            raise CustomValidationException({"message":"email or password is invalid"}, 401)
            #exceptions.AuthenticationFailed(res_data)

        return data

class EmailValidationSerializer(serializers.Serializer):
    email_address = serializers.CharField(required = True)
    def validate_email_address(self, data):
        try:
            request = self.context.get('request')

            user = Account.objects.get(email=data)
        except (ValueError, Account.DoesNotExist):
            raise CustomValidationException({"message":"Invalid user email"}, 400)
        if user :
            domain = f"{request.scheme}://{request.META.get('HTTP_HOST')}"
            send_reset_account_password.delay(domain, user.id)

        return user

class Validate_Token:
    def __init__(self, request):
        self.request = request

    def validate_token_and_user(self, uidb64, token):

        try:
            uid = urlsafe_base64_decode(uidb64).decode()

            user = Account.objects.get(pk=uid)

        except (ValueError, Account.DoesNotExist):
            raise CustomValidationException({"message":"Invalid user ID"}, 401)

        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            raise CustomValidationException ({"message":"Token has Expired"}, 401)

        return user


class PasswordValidationSerializer(serializers.Serializer):
    email = serializers.CharField(required = True)
    password = serializers.CharField(write_only = True,required = True)
    token = serializers.CharField(required = True)

    def validate_password(self, value):

        if len(value) < 8:
            raise CustomValidationException({"message": "Password must be at least 8 characters long."}, 400)
        if not re.search(r"[A-Za-z]", value):
            raise CustomValidationException({"message":"Password must contain at least one letter."}, 400)
        if not re.search(r"\d", value):
            raise CustomValidationException({"message":"Password must contain at least one number."}, 400)
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise CustomValidationException({"message":"Password must contain at least one special character."}, 400)
        return value


    def validate(self, data):

        user = Account.objects.get(email = data['email'])

        token_generator = PasswordResetTokenGenerator()


        if not token_generator.check_token(user, data['token']):
            raise CustomValidationException({"message":"Token has Expired"}, 400)


        return data


class CreateGroupSerializer(serializers.Serializer):
    name = serializers.CharField()
    permissions = serializers.ListField(
        child=serializers.CharField(),  # List of permission codenames
        allow_empty=True,
    )
    model_name = serializers.CharField()


class AddUserToGroupSerializer(serializers.Serializer):
    email = serializers.CharField()
    group_name = serializers.CharField()

    def validate(self, data):
        # Check if the user exists
        try:
            user = Account.objects.get(email=data['email'])
        except Account.DoesNotExist:
            raise CustomValidationException({"email": f"User '{data['email']}' does not exist."}, 400)

        # Check if the group exists
        try:
            group = Group.objects.get(name=data['group_name'])
        except Group.DoesNotExist:
            raise CustomValidationException({"group_name": f"Group '{data['group_name']}' does not exist."}, 400)

        data['user'] = user
        data['group'] = group
        return data
