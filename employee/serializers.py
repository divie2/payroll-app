from rest_framework import serializers
from .models import Employee, NextOfKin, Team, PayrollStaff, Rate, Payslip, LoanRequest, Tax, Debt
from account.utills import send_reset_account_password
from account.perms import CustomValidationException
from datetime import date
import logging

logger = logging.getLogger("employee")

def format_datetime(dt):
    # Get the day of the month
    day = dt.day

    # Determine the correct ordinal suffix
    if 11 <= day <= 13:  # Special case for 11th, 12th, 13th
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")

    # Format the date
    return dt.strftime(f"%A, %B {day}{suffix}, %Y")

class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ["name"]

class NOKSerializer(serializers.ModelSerializer):
    class Meta:
        model = NextOfKin
        fields = ["name", "address", "phone"]

class EmployeeGetSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(source='account.fullname', read_only=True)
    email = serializers.CharField(source='account.email', read_only=True)
    next_of_kin = NOKSerializer(source="nok", read_only=True)
    class Meta:
        model = Employee
        fields = ["fullname", "email", "status", "jira_ticket_id", "jira_employee_id", "base_pay", "pay_deno", "acct_num", "acct_name", "bank_name", "job_role", "job_type", "phone", "start_date", "dob", "id_type", "address", "next_of_kin"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.members.all():
            data['team'] = instance.members.all()[0].name
        return data

class EmployeeUpdateGetSerializer(serializers.ModelSerializer):
    fullname = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    team_id =  serializers.CharField(required=False)
    nok_name = serializers.CharField(required=False)
    nok_address = serializers.CharField(required=False)
    nok_phone = serializers.CharField(required=False)
    class Meta:
        model = Employee
        fields = ["fullname", "email", "status", "jira_ticket_id", "jira_employee_id", "base_pay", "pay_deno", "acct_num", "acct_name", "bank_name", "job_role", "job_type", "phone", "start_date", "dob", "id_type", "address", "team_id", "nok_name", "nok_address", "nok_phone"]


    def update_nok(self, instance, validated_data):
        if instance.nok:
            nok = instance.nok
            nok.name = validated_data.get('nok_name', nok.name)
            nok.address = validated_data.get('nok_address', nok.address)
            nok.phone = validated_data.get('nok_phone', nok.phone)
            nok.save()
        else:
            if validated_data.get('nok_name') and validated_data.get('nok_address') and validated_data.get('nok_phone'):
                try:
                    NextOfKin.objects.create(name=validated_data.get('nok_name'), address=validated_data.get('nok_address'), phone=validated_data.get('nok_phone'), employee=instance)
                except Exception as e:
                    logger.error(f"Error creating next of kin- {e}")
                    raise CustomValidationException({"message": "Failed to create employee"})

    def update_account(self, instance, validated_data, request):
        domain = f"{request.scheme}://{request.META.get('HTTP_HOST')}"

        if validated_data.get("fullname") or validated_data.get("email"):
            fullname = validated_data.get("fullname", instance.account.fullname)
            email = validated_data.get("email", instance.account.email)
            account = instance.account
            original_email = account.email
            account.fullname = fullname
            account.email = email
            account.is_active = account.email == original_email
            account.save()

            if account.email != original_email:
                account.is_active = False
                account.save()
                send_reset_account_password.delay(domain, account.id)

    def update_employee_team(self, validated_data, employee):
        team_id = validated_data.get("team_id")
        if team_id:
            related_team = Team.objects.filter(pk = team_id).first()
            prev_team = employee.members.first()
            if related_team and prev_team:
                prev_team.members.remove(employee)
                prev_team.save()

                # now we can add the employee to new team yeah
                related_team.members.add(employee)
                related_team.save()

    def update(self, instance, validated_data):
        request = self.context.get('request')
        # update the account
        self.update_account(instance, validated_data, request)

        # update the nok
        self.update_nok(instance, validated_data)

        # update employee team
        if validated_data.get("team_id"):
            self.update_employee_team(validated_data, instance)

        # save employee details via the use rof **validated_data
        instance = super().update(instance, validated_data)

        # instance.save()
        return instance

class UpdatePayrollStaffStatusSerializer(serializers.ModelSerializer):

    class Meta:
        model = PayrollStaff
        fields = ["status"]

    def update(self, instance, data):
        # save payrollstaff details via the use rof **validated_data
        instance = super().update(instance, data)

        # instance.save()
        return instance

class ListEmployeeSerializer(serializers.ModelSerializer):
    """Serializer for List Employee"""
    email = serializers.CharField(source='account.email')
    fullname = serializers.CharField(source='account.fullname')
    nok_name = serializers.CharField(source='nok.name')
    nok_address = serializers.CharField(source='nok.address')
    nok_phone = serializers.CharField(source='nok.phone')


    class Meta:
        model = Employee
        fields = ["id",'jira_ticket_id','base_pay', 'job_role','job_type', 'pay_deno', 'phone', 'dob', 'fullname', 'email', 'acct_num', 'bank_name', 'address','jira_employee_id', 'id_type','start_date', 'acct_name', 'nok_name', 'nok_address', 'nok_phone',
                  ]
        read_only_fields = ['id']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.members.all():
            data['team'] = instance.members.all()[0].name
        return data

class CreateTeamSerializer(serializers.ModelSerializer):
    """Serializer for Team creation """

    class Meta :
        model = Team
        fields = ["name", "lead"]

    # def validate_lead(self, data):

    #     # Validate the lead (if provided)
    #     lead_id = data.get("lead")
    #     if lead_id:
    #         lead = Employee.objects.filter(pk=lead_id)

    #         if not lead.exists():
    #             raise CustomValidationException(
    #                 {"message": "The team lead does not exist"}, 400
    #             )

    #     return lead.first()

    def validate(self, data):

        existing_team = Team.objects.filter(name=data.get('name'))
        if existing_team :
            raise CustomValidationException({"message": "The team already exist"}, 400)

        return data

    def create(self, validated_data):
        # Create and return the Team instance

        return Team.objects.create(**validated_data)

class ListTeamSerializer(serializers.ModelSerializer):
    """Serializer for Team creation """

    class Meta :
        model = Team
        fields = ["id", "name", "lead"]
        read_only_fields = ["id", 'name', 'lead']

class UpdateTeamSerializer(serializers.ModelSerializer):
    """Serializer for Team Update"""

    lead = serializers.CharField(required = False)

    class Meta :
        model = Team
        fields = ["id", "name", "lead"]
        read_only_fields = ["id", "name"]

    def validate_lead(self, data):

            try :

                filtered_lead = Employee.objects.get(pk = data)

                return filtered_lead
            except Employee.DoesNotExist:
                raise CustomValidationException({"message": "The team lead does not exist"}, 400)


    def update(self, instance, validated_data):

            lead_id = validated_data.pop('lead', None)

            if lead_id:
                    instance.lead = lead_id

            # Update other fields (if any)
            instance = super().update(instance, validated_data)

            return instance

class LoanRequestSerializer(serializers.ModelSerializer):
    """Serializer for Loan Request"""

    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    employee = serializers.CharField()
    purpose = serializers.CharField(max_length=255)
    due_date = serializers.DateField()


    class Meta:
        model = LoanRequest
        fields = ["amount", "purpose", "due_date", "employee", "status"]
        read_only_fields = ["id", "status"]

    def validate_employee(self, data):
            try :
                filtered_employee = Employee.objects.get(pk = data)
                return filtered_employee
            except Employee.DoesNotExist:
                raise CustomValidationException({"message": "The employee does not exist"}, 400)

    def validate_amount(self, value):
        """
        Validate that the amount is positive.
        """
        if value <= 0:
            raise CustomValidationException({"message": "Amount must be greater than zero"}, 400)
        return value

    def validate_due_date(self, value):
        """
        Validate that the due date is in the future.
        """

        if value <= date.today():
            raise CustomValidationException({"message": "Due date must be in the future"}, 400)
        return value

    def create(self, validated_data):
        """
        Create and return a new LoanRequest instance.
        """
        return LoanRequest.objects.create(**validated_data)

class UpdateLoanSerializerAdmin(serializers.ModelSerializer):

    """serializer For updating loan requests"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    purpose = serializers.CharField(max_length=255)
    due_date = serializers.DateField(required=True)
    status = serializers.CharField(required=True)

    class Meta:
        model = LoanRequest
        fields = ["amount", "purpose", "due_date", "status"]
        read_only_fields = ["id", "employee"]

    def validate_employee(self, data):
        try :

                filtered_lead = Employee.objects.get(pk = data)

                return filtered_lead
        except Employee.DoesNotExist:
                raise CustomValidationException({"message": "The employee does not exist"}, 400)

    def validate_amount(self, value):
        """
        Validate that the amount is positive.
        """
        if value <= 0:
            raise CustomValidationException({"message": "Amount must be greater than zero"}, 400)
        return value

    def validate_due_date(self, value):
        """
        Validate that the due date is in the future.
        """

        if value <= date.today():
            raise CustomValidationException({"message": "Due date must be in the future"}, 400)
        return value


    def update(self, instance, validated_data):

            if "amount" in validated_data:
                amount_id = validated_data.pop('amount', None)

                instance.amount = amount_id

            if "purpose" in validated_data:
                purpose_id = validated_data.pop('purpose', None)

                instance.purpose = purpose_id

            if "due_date" in validated_data:
                due_date_id = validated_data.pop('due_date', None)

                instance.due_date = due_date_id

            if "status" in validated_data:
                status_id = validated_data.pop('status', None)

                instance.status = status_id


            # Update other fields (if any)
            instance = super().update(instance, validated_data)

            return instance


class UpdateLoanSerializer(serializers.ModelSerializer):

    """serializer For updating loan requests"""
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    purpose = serializers.CharField(max_length=255)
    due_date = serializers.DateField(required=True)

    class Meta:
        model = LoanRequest
        fields = ["amount", "purpose", "due_date", "status"]
        read_only_fields = ["id", "status", "employee"]

    def validate_employee(self, data):
        try :

                filtered_lead = Employee.objects.get(pk = data)

                return filtered_lead
        except Employee.DoesNotExist:
                raise CustomValidationException({"message": "The employee does not exist"}, 400)

    def validate_amount(self, value):
        """
        Validate that the amount is positive.
        """
        if value <= 0:
            raise CustomValidationException({"message": "Amount must be greater than zero"}, 400)
        return value

    def validate_due_date(self, value):
        """
        Validate that the due date is in the future.
        """

        if value <= date.today():
            raise CustomValidationException({"message": "Due date must be in the future"}, 400)
        return value


    def update(self, instance, validated_data):

        if "approved" not in instance.status and "not approved" not in instance.status:

            if "amount" in validated_data:
                amount_id = validated_data.pop('amount', None)

                instance.amount = amount_id

            if "purpose" in validated_data:
                purpose_id = validated_data.pop('purpose', None)

                instance.purpose = purpose_id

            if "due_date" in validated_data:
                due_date_id = validated_data.pop('due_date', None)

                instance.due_date = due_date_id


            # Update other fields (if any)
            instance = super().update(instance, validated_data)

            return instance

class ListEmployeeLoanSerializer(serializers.ModelSerializer):
    """serializer for listing loan requests"""

    class Meta:
        model = LoanRequest
        fields = ["id", "employee", "status", "purpose", "due_date", "amount"]

class RateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        fields = ["id", "official_rate", "parallel_rate"]

class SetRateserializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        fields = ["official_rate", "parallel_rate"]

class PayslipSerializer(serializers.ModelSerializer):
    employee = EmployeeGetSerializer()
    tax = serializers.CharField(source="tax.tax_amount_monthly")
    class Meta:
        model = Payslip
        fields = ["employee", "official_base_pay", "parallel_base_pay", "paid", "created", "tax", "debt"]

class TaxSerializer(serializers.ModelSerializer):
    payslip = PayslipSerializer()
    class Meta:
        model = Tax
        fields = ['payslip', "tax_amount_monthly", "tax_amount_yearly", "created", "remmited", 'date_remmited']

    def get_created(self, obj):
        return format_datetime(obj.created)
    
    def get_date_remmited(self, obj):
        date_remmitted = obj.date_remmited
        if date_remmitted:
            return format_datetime(date_remmitted)
        return date_remmitted

class DebtSerializer(serializers.ModelSerializer):
    payslips = PayslipSerializer(many=True)
    class Meta:
        model = Debt
        fields = ['payslips', "employee", "total_owned", "paid_so_far", "percentage_deduction", "balance", "status", "purpose"]

class UpdateDebtSerializer(serializers.ModelSerializer):

    class Meta:
        model = Debt
        fields = ["total_owned","paid_so_far", "percentage_deduction", "balance", "status", "purpose"]

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        return instance