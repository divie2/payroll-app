
from .rates import get_parallel_rate, get_official_exchange_rate
from .models import Rate, Employee
from django.utils import timezone
from django.conf import settings
from account.perms import CustomValidationException
from .tax_calculator import calculate_tax

import logging

RATE_GEN_DAY = int(settings.RATE_GEN_DAY)

logger = logging.getLogger(__name__)



def get_current_month_rate():
    official_rate = get_official_exchange_rate()
    parallel_rate = get_parallel_rate()
    current_month_rate = Rate.objects.create(official_rate=float(official_rate), parallel_rate=float(parallel_rate))
    return current_month_rate


def get_employee_tax(employee: Employee) -> tuple[float, float, float, float]:
    if employee.pay_deno == "Dollars":
        today = timezone.now().date()
        current_month_rate = Rate.objects.filter(
            created__year=today.year, created__month=today.month
        ).first()
        
        if not current_month_rate: # generate rate for the month on today's date
            current_month_rate = get_current_month_rate()

        if not current_month_rate:
            raise CustomValidationException({"message": "Rates are not available for this month."}, 400)
        print(employee.base_pay, current_month_rate.official_rate, current_month_rate.parallel_rate)
        official_base_pay = employee.base_pay * current_month_rate.official_rate
        parallel_base_pay = employee.base_pay * current_month_rate.parallel_rate
    else:
        official_base_pay = parallel_base_pay = employee.base_pay
    tax_amount_yearly, tax_amount_monthly = calculate_tax(official_base_pay)
    
    return official_base_pay, parallel_base_pay, tax_amount_yearly, tax_amount_monthly
