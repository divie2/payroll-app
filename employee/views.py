from .models import Employee, LoanRequest, Team
from .perms import IsAuthenticatedAndCRUDEmployee, CustomValidationException, IsPayrollStaff, IsAuthenticatedAndChangePayrollStaff
from rest_framework.response import Response
from rest_framework import status
from .serializers import EmployeeGetSerializer, EmployeeUpdateGetSerializer, UpdatePayrollStaffStatusSerializer, RateSerializer, SetRateserializer, CreateTeamSerializer, ListTeamSerializer, TaxSerializer, DebtSerializer, UpdateDebtSerializer
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from .models import PayrollStaff, Payslip, Tax, Rate, Debt
from .utils import get_current_month_rate
from django.utils import timezone
from django.conf import settings
import logging
from account.perms import IsAuthenticatedAndNotBlacklisted
from django.core.mail import send_mail
from .serializers import ListEmployeeSerializer,UpdateTeamSerializer, LoanRequestSerializer, ListEmployeeLoanSerializer, UpdateLoanSerializer,UpdateLoanSerializerAdmin
from rest_framework.viewsets import ReadOnlyModelViewSet
from celery.result import AsyncResult
from .tasks import generate_payslip_for_employee, generate_payslips_for_all_employees, deduct_employee_debts

RATE_GEN_DAY = int(settings.RATE_GEN_DAY)

logger = logging.getLogger(__name__)


class EmployeeView(APIView):
    # Default permission for all methods
    permission_classes = [IsAuthenticatedAndCRUDEmployee]

    def get(self, request, employee_id):
        try:
            employee = Employee.objects.get(pk=employee_id)
            serializer = EmployeeGetSerializer(employee)
            return Response({"message": "Data fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            return Response({"message": "Invalid Employee Id"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, employee_id):
        try:
            employee = Employee.objects.get(pk=employee_id)
            account = employee.account
            account.delete()
            employee.delete()
            return Response({"message": "Employee and Account deleted successfully"}, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            return Response({"message": "Invalid Employee Id"}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, employee_id):
        try:
            employee = Employee.objects.get(pk=employee_id)
            serializer = EmployeeUpdateGetSerializer(employee, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message": "Employee updated successfully"}, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            return Response({"message": "Invalid Employee Id"}, status=status.HTTP_400_BAD_REQUEST)

class FilterEmployeeView(APIView):
    permission_classes = [IsAuthenticatedAndCRUDEmployee]

    def get(self, request):
        # get filter parameters in the query by name, job_type, job_role, base_pay, team, status
        name = request.query_params.get('name')
        job_type = request.query_params.get('job_type')
        job_role = request.query_params.get('job_role')
        base_pay = request.query_params.get('base_pay')
        team = request.query_params.get('team')
        emp_status = request.query_params.get('emp_status')
        employees = Employee.objects.all()
        if name:
            employees = employees.filter(account__fullname__icontains=name)
        if job_type:
            employees = employees.filter(job_type=job_type)
        if job_role:
            employees = employees.filter(job_role__icontains=job_role)
        if base_pay:
            employees = employees.filter(base_pay=base_pay)
        if team:
            employees = employees.filter(team__name=team)
        if emp_status:
            employees = employees.filter(status=emp_status)

        serializer = EmployeeGetSerializer(employees, many=True)
        return Response({"message": "Data fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)

class EmployeeUpgradeView(APIView):
    permission_classes = [IsAuthenticatedAndChangePayrollStaff]

    def post(self, request, employee_id):
        """This add an employee to p[ayroll staff table"""
        try:
            employee = Employee.objects.get(pk=employee_id)
            PayrollStaff.objects.get_or_create(employee=employee)
            return Response({"message": "Employee added as payroll staff"}, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            return Response({"message": "Invalid Employee Id"}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, employee_id):
        """This just remove an amployee from payrollstaff table"""
        try:
            employee = Employee.objects.get(pk=employee_id)
            payroll_staff = PayrollStaff.objects.get(employee=employee)
            payroll_staff.delete()
            return Response({"message": "Employee removed as payroll staff"}, status=status.HTTP_200_OK)
        except Employee.DoesNotExist:
            return Response({"message": "Invalid Employee Id"}, status=status.HTTP_400_BAD_REQUEST)
        except PayrollStaff.DoesNotExist:
            return Response({"message": "Employee is not a payroll staff"}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, employee_id):
        """This update the employee payroll staff status"""
        try:
            employee = Employee.objects.get(pk=employee_id)
            payroll_staff = employee.payroll_staff
            print(payroll_staff)
            if payroll_staff:
                serializer = UpdatePayrollStaffStatusSerializer(payroll_staff, data = request.data, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response({"message": "status updated successfully"}, status=status.HTTP_200_OK)
            return Response({"message": "employee payroll staff does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Employee.DoesNotExist:
            return Response({"message": "Invalid Employee Id"}, status=status.HTTP_400_BAD_REQUEST)

class EmployeePaysliplView(APIView):
    permission_classes = [IsPayrollStaff]

    def post(self, request, employee_id):
        """Generate payslip for an employee for the current month as a Celery background task."""
        try:
            task = generate_payslip_for_employee.delay(employee_id)
            return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)
        except Employee.DoesNotExist:
            logger.error(f"Employee not found: {employee_id}")
            return Response({"message": "Employee not synced from Jira or Employee is not active"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"error generating Payslip for an employee - {e}")
            raise CustomValidationException({"message": "Payslip failed to generate"}, 500)


    def get(self, request):
        """Generate payslips for all employees for the current month as a Celery background task."""
        task = generate_payslips_for_all_employees.delay()
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)

    def delete(self, request):
        """This delete current month generated payslips ASAP"""
        try:
            today = timezone.now().date()
            payslips = Payslip.objects.filter(created__month=today.month)
            payslips.delete()
            return Response({"message": "Current month payslips deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"error deleting Payslip for all employees - {e}")
            raise CustomValidationException({"message": "Payslips failed to delete"}, 500)

class EmployeeViewSet(ReadOnlyModelViewSet):

    permission_classes = [IsAuthenticatedAndCRUDEmployee]

    queryset = Employee.objects.all()
    serializer_class = ListEmployeeSerializer

    def list(self, request, *args, **kwargs):
        """Return a custom response for the list of employees."""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"employees": serializer.data})

class TaskStatusView(APIView):
    permission_classes = [IsPayrollStaff]
    def get(self, request, task_id):
        """Check the status of a Celery task. because why not??? na for payslip(s) sha oooo"""
        task_result = AsyncResult(task_id)
        response_data = {
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result
        }
        task_status  = status.HTTP_200_OK
        if task_result.result.get("message") == "Payslip failed to generate":
            task_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            response_data['status'] = "Failed"
        return Response(response_data, status=task_status)

class EmployeeTeamCreate(APIView):
    # Default permission for all methods
    permission_classes = [IsAuthenticatedAndCRUDEmployee]


    def post(self, request):

        """This would be used to create new teams"""
        serializer = CreateTeamSerializer(data = request.data)

        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({'message': 'Team Created !'}, status=status.HTTP_200_OK)

        except CustomValidationException as e:
            return Response(e.to_res(), 400)

        # except Exception as e:
        #     logger.error(f"Error: {e}")
        #     return Response({"error": f"{e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListTeam(APIView):
    # Default permission for all methods
    permission_classes = [IsAuthenticatedAndCRUDEmployee]


    def get(self, request):

        """List teams"""
        teams = Team.objects.all()

        if not teams.exists():
            return Response(
                {"message": "No teams found", "data": []},
                status=status.HTTP_200_OK)
        serializer = ListTeamSerializer(teams, many=True)
        return Response({"message": "Data fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)

class DeleteTeams(APIView):

    permission_classes = [IsAuthenticatedAndCRUDEmployee]

    """ To delete teams """

    def delete(self, request):
        """"Delete team"""

        try:
            team_name = request.data.get("name")  # Extract the team name correctly
            team = Team.objects.get(name=team_name)

            team.delete()
            return Response({"message": "Team deleted successfully"}, status=status.HTTP_200_OK)
        except Team.DoesNotExist:
            return Response({"message": "Invalid Team name"}, status=status.HTTP_400_BAD_REQUEST)

class UpdateTeam(APIView):
    permission_classes = [IsAuthenticatedAndCRUDEmployee]

    def patch(self, request, team_id):

        """"Na only admins wey get power fit update teams"""

        try:
            team = Team.objects.get(pk = team_id)
            serializer = UpdateTeamSerializer(team, data = request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message": "Team Updated successfully"}, status=status.HTTP_200_OK)
        except Team.DoesNotExist:
            return Response({"message": "Invalid Team name"}, status=status.HTTP_400_BAD_REQUEST)
        except CustomValidationException as e:
            return Response(e.to_res(), 400)

class EmployeeLoanRequest(APIView):
    permission_classes = [IsAuthenticatedAndNotBlacklisted]
    """na here dem employees dem go fit request for loan"""

    def post(self, request):

        """Loan Request"""
        
        serializer =LoanRequestSerializer(data = request.data)

        try:
            serializer.is_valid(raise_exception=True)
            loan_request = serializer.save()
            # print(loan_request)

            try:
                subject = "Loan Request Created"
                message = f"Hi {loan_request.employee.account.fullname} your loan request has been created!"
                recipient_list = [loan_request.employee.account.email]
                send_mail(subject, message, None, recipient_list, fail_silently=False)

            except Exception as email_error:

                logger.error(f"Failed to send email for loan request {loan_request.id}: {email_error}")

            return Response({'message': 'Loan Request Created'}, status=status.HTTP_200_OK)


        except CustomValidationException as e:
                return Response(e.to_res(), 400)

class EmployeeLoanRequestList(APIView):

    permission_classes = [IsAuthenticatedAndChangePayrollStaff]
    """na only payroll staff fit see loan list"""

    def get(self, request):

            loans = LoanRequest.objects.all()

            if not loans.exists():
                return Response(
                    {"message": "No loans found", "data": []},
                    status=status.HTTP_200_OK)

            serializer = ListEmployeeLoanSerializer(loans, many=True)
            return Response({"message": "Data fetched successfully", "data": serializer.data}, status=status.HTTP_200_OK)

class EmployeeUpdateLoan(APIView):
    permission_classes = [IsAuthenticatedAndNotBlacklisted]

    def patch(self,request,loan_id):

        """ Na user fit update loan  """

        try:
            loan = LoanRequest.objects.get(pk = loan_id)
            serializer = UpdateLoanSerializer(loan, data = request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message": "Loan Updated successfully"}, status=status.HTTP_200_OK)
        except LoanRequest.DoesNotExist:
            return Response({"message": "Invalid Loan name"}, status=status.HTTP_400_BAD_REQUEST)
        except CustomValidationException as e:
            return Response(e.to_res(), 400)

class EmployeeUpdateLoanAdmin(APIView):
    permission_classes = [IsAuthenticatedAndChangePayrollStaff]

    def patch(self,request,loan_id):

        """"Update loan by admin"""

        try:
            loan = LoanRequest.objects.get(pk = loan_id)
            serializer = UpdateLoanSerializerAdmin(loan, data = request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"message": "Loan Updated successfully"}, status=status.HTTP_200_OK)
        except LoanRequest.DoesNotExist:
            return Response({"message": "Invalid Loan name"}, status=status.HTTP_400_BAD_REQUEST)
        except CustomValidationException as e:
            return Response(e.to_res(), 400)

@api_view(['GET'])
@permission_classes([IsPayrollStaff])
def current_month_rate(request) -> Response:
    try:
        today = timezone.now().date()
        this_month_rate = Rate.objects.filter(
            created__year=today.year, created__month=today.month
        ).first()

        if not this_month_rate: # generate rate for the month on today's date
            this_month_rate = get_current_month_rate()
        serializer = RateSerializer(this_month_rate)
        return Response({"message":"Successfully fetch rate", "data": serializer.data}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Falied to get rate {e}")
        return Response({"error": "Falied to get rate"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PATCH'])
@permission_classes([IsPayrollStaff])
def SetRate(request, rate_id:str) -> Response:
    """This na to just update rate incase una company no fit pay for the automatic rate pulled sha"""
    try:
        rate = Rate.objects.get(pk=rate_id)
        serializer = SetRateserializer(rate, data = request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Rate updated successfully", "date": serializer.data})
    except Rate.DoesNotExist:
        return Response({"error": f"No rate with id {rate_id}"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Falied to update rate {e}")
        return Response({"error": "Falied to update rate"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticatedAndCRUDEmployee])
def get_employee_taxes(request, employee_id):
    """This help grab the taxes genrated and deducted from an employee - an employee should only see own while payroll admin can see all"""
    try:
        related_employee = Employee.objects.get(pk=employee_id)
        related_taxes = Tax.objects.filter(payslipp__employee = related_employee)
        serializer = TaxSerializer(related_taxes, many=True)
        return Response({"success": "Taxes fetched successfully", "data": serializer.data})
    except Employee.DoesNotExist:
        return Response({"error": "employee do not exist"}, status = status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
@permission_classes([IsPayrollStaff])
def get_all_employee_taxes(request):
    """This help grab the taxes genrated and deducted from all employees - an employee should only see own while payroll admin can see all"""
    try:
        related_taxes = Tax.objects.order_by("payslip__employee")
        serializer = TaxSerializer(related_taxes, many=True)
        return Response({"success": "Taxes fetched successfully", "data": serializer.data})
    except Employee.DoesNotExist:
        return Response({"error": "employee do not exist"}, status = status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
@permission_classes([IsPayrollStaff])
def deduct_employees(request):
    """This deduct the monthly debt from employee payslip"""
    # let send this over to celery ->>>> many employee might be paying debt ....country harddddd
    task_id = deduct_employee_debts.delay()
    return Response({"message": "debt is now being deducted", "task_id": task_id}, status=status.HTTP_202_ACCEPTED)


@api_view(["GET"])
@permission_classes([IsPayrollStaff])
def get_employees_debts(request):
    """Let's get the debts details"""
    try:
        all_debts = Debt.objects.all()
        serializer = DebtSerializer(all_debts, many=True)
        return Response({"message": "debt fetched successfully", "debts": serializer.data})
    except Exception as e:
        logger.error(f"Error getting debts - {e}")
        raise CustomValidationException({"message": "Server Error"}, 500)


@api_view(["PATCH"])
@permission_classes([IsPayrollStaff])
def update_employee_debt(request, debt_id):
    """This will help payroll admin adjust some things on the debt row attached to an employee...make payroll admin no take bribe sha"""
    try:
        related_debt = Debt.objects.get(pk=debt_id)
        serializer = UpdateDebtSerializer(related_debt, data = request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response({"success": "debt updated successfully"})
    except Debt.DoesNotExist:
        return Response({"error": "debt not found"}, status = status.HTTP_404_NOT_FOUND)

