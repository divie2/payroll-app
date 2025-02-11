from celery import shared_task
from django.utils import timezone
from .models import Employee, Payslip, Tax, Rate, Debt
from .utils import get_employee_tax, get_current_month_rate
from .serializers import PayslipSerializer
import logging
from django.db.models import Q


logger = logging.getLogger(__name__)


def deduct_monthly_debt(debts):
    today = timezone.now().date()
    for debt in debts:
        if debt.total_owned != debt.paid_so_far:
            # get the related employee
            related_employee = debt.employee
            base_pay = related_employee.base_pay
            # get the employee current month payslip ---> this expects the current month payslips to have been generated
            # Fetch or create the current month payslip
            current_month_payslip = Payslip.objects.filter(employee=related_employee, created__month=today.month,created__year=today.year).first()
            if current_month_payslip:
                to_pay = current_month_payslip.parallel_base_pay * (debt.percentage_deduction / 100)
                if to_pay > debt.balance:
                    to_pay = debt.balance
                current_month_payslip.net_pay = current_month_payslip.net_pay - to_pay
                current_month_payslip.debt = to_pay
                current_month_payslip.save()

                debt.payslips.add(current_month_payslip)
                debt.paid_so_far = debt.paid_so_far + to_pay
                debt.balance = debt.total_owned - debt.paid_so_far
                debt.last_deducted = today
                if debt.balance == 0:
                    debt.status = "inactive"
        else:
            debt.status = "inactive"
        debt.save()
    return "debt deduction process completed"

@shared_task
def generate_payslip_for_employee(employee_id):
    try:
        today = timezone.now().date()
        employee = Employee.objects.get(pk=employee_id, status="active")
        existing_payslip = Payslip.objects.filter(employee=employee, created__month=today.month, created__year=today.year)
        if existing_payslip.exists():
            serializer = PayslipSerializer(existing_payslip.first())
            return {"message": "Already generated payslip for this month is returned", "payslip": serializer.data}
        
        official_base_pay, parallel_base_pay, tax_amount_yearly, tax_amount_monthly = get_employee_tax(employee)
        new_payslip = Payslip.objects.create(
            employee=employee, official_base_pay=official_base_pay, parallel_base_pay=parallel_base_pay
        )
        Tax.objects.create(payslip=new_payslip, tax_amount_monthly=tax_amount_monthly, tax_amount_yearly=tax_amount_yearly)
        new_payslip.refresh_from_db()
        serializer = PayslipSerializer(new_payslip)
        return {"message": "Payslip generated successfully", "payslip": serializer.data}
    
    except Employee.DoesNotExist:
        logger.error(f"Employee not found: {employee_id}")
        return {"message": "Employee not synced from Jira or Employee is not active"}
    except Exception as e:
        logger.error(f"error generating Payslip for an employee - {e}")
        return {"message": "Payslip failed to generate"}

@shared_task
def generate_payslips_for_all_employees():
    try:
        today = timezone.now().date()
        existing_payslips = Payslip.objects.filter(created__month=today.month, created__year=today.year)
        if existing_payslips.exists():
            serializer = PayslipSerializer(existing_payslips, many=True)
            return {"message": "Payslips already generated for this month"}
        
        employees = Employee.objects.filter(status="active")
        for employee in employees:
            official_base_pay, parallel_base_pay, tax_amount_yearly, tax_amount_monthly = get_employee_tax(employee)
            gross_pay = parallel_base_pay
            net_pay = gross_pay - tax_amount_monthly
            new_payslip = Payslip.objects.create(
                employee=employee, official_base_pay=official_base_pay, parallel_base_pay=parallel_base_pay, net_pay=net_pay, gross_pay=gross_pay
            )
            Tax.objects.create(payslip=new_payslip, tax_amount_monthly=tax_amount_monthly, tax_amount_yearly=tax_amount_yearly)
            related_debts = Debt.objects.filter(employee = employee, status = "active").exclude(last_deducted__month = today.month)
            if related_debts:
                deduct_monthly_debt(related_debts)

        
        payslips = Payslip.objects.filter(created__month=today.month, created__year=today.year)
        serializer = PayslipSerializer(payslips, many=True)
        return {"message": "Payslips generated successfully", "payslips": serializer.data}
    except Exception as e:
        logger.error(f"error generating Payslip for all employees - {e}")
        return {"message": "Payslip failed to generate"}

@shared_task
def generate_rate_on_16th():
    try:
        today = timezone.now().date()
        current_month_rate = Rate.objects.filter(
            created__year=today.year, created__month=today.month
        ).first()
        
        if not current_month_rate: # generate rate for the month on today's date
            current_month_rate = get_current_month_rate()

        return current_month_rate.official_rate, current_month_rate.parallel_rate, current_month_rate.created
    except Exception as e:
        logger.error(f"error generating rate - {e}")
        return {"message": "Rate failed to generate"}
    


@shared_task
def deduct_employee_debts():
    try:
        today = timezone.now().date()
        debts = Debt.objects.filter(status = "active").exclude(last_deducted__month = today.month)
        res = deduct_monthly_debt(debts)
        return {"message": res}
    except Exception as e:
        return {"error": "Failed to deduct debt"}
