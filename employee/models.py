from django.db import models
from account.models import Account
from account.perms import CustomValidationException
from django.utils import timezone


class Employee(models.Model):
    EMPLOYEE_STATUS = (("active", "active"), ("former", "former"), ("suspended", "suspended"))
    DENO_TYPE = (("Dollars", "Dollars"), ("Naira", "Naira"))
    JOB_TYPE = (("Full Time", "Full Time"), ("Part Time", "Part Time"))
    account = models.OneToOneField(Account, on_delete=models.CASCADE, related_name='account')
    status = models.CharField(max_length=20, choices=EMPLOYEE_STATUS, default="active")
    jira_ticket_id = models.CharField(max_length=20)
    jira_employee_id = models.CharField(max_length=20)
    base_pay = models.FloatField()
    pay_deno = models.CharField(max_length=20, choices=DENO_TYPE, default='Naira')
    acct_num = models.CharField(max_length=30, blank=True)
    acct_name = models.CharField(max_length=250, blank=True)
    bank_name = models.CharField(max_length=250, blank=True)
    job_role = models.CharField(max_length=500)
    job_type = models.CharField(max_length=20, choices=JOB_TYPE, default="Full Time")
    phone = models.CharField(max_length=20)
    start_date = models.DateField()
    address = models.CharField()
    dob = models.DateField()
    tax_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    id_type = models.CharField(max_length=200)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.account.fullname}"


class Team(models.Model):
    name = models.CharField(max_length=500, unique=True)
    lead = models.OneToOneField(Employee, on_delete=models.SET_NULL, blank=True, related_name='team_lead', null=True)
    members = models.ManyToManyField(Employee, related_name='members', blank=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class LoanRequest(models.Model):
    LOAN_STATUS = (("approved", "approved"), ("pending", "pending"), ("not approved", "not approved"))
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, related_name='loan_request')
    amount = models.PositiveIntegerField()
    purpose = models.TextField(max_length=500)
    due_date = models.DateField()
    status = models.CharField(choices=LOAN_STATUS, default="pending",  blank=True)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        try:
            return f"{self.employee.account.fullname}'s Loan Request"
        except AttributeError:
            return f"Loan Request {self.id}"


class NextOfKin(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='nok')
    name = models.CharField(max_length=500)
    address = models.CharField()
    phone = models.CharField(max_length=20)


class PayrollStaff(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='payroll_staff')
    status = models.CharField(max_length=20, choices=Employee.EMPLOYEE_STATUS, default="active")
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.employee.account.fullname


class Payslip(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslip')
    pay_date = models.DateField(blank=True, null=True)
    official_base_pay = models.FloatField()
    parallel_base_pay = models.FloatField()
    net_pay = models.FloatField()
    gross_pay = models.FloatField()
    debt = models.FloatField(blank=True, default=0.0)
    paid = models.BooleanField(default=False)
    created = models.DateField(default=timezone.now)
    updated = models.DateField(default=timezone.now)

    def __str__(self):
        return self.employee.account.fullname


class Tax(models.Model):
    payslip = models.OneToOneField(Payslip, on_delete=models.CASCADE, related_name='tax')
    tax_amount_monthly = models.FloatField()
    tax_amount_yearly = models.FloatField()
    remmited = models.BooleanField(default=False)
    date_remmited = models.DateField(blank=True, null=True)
    created = models.DateField(default=timezone.now)
    updated = models.DateField(default=timezone.now)

    class Meta:
        verbose_name_plural = "Taxes"

    def __str__(self):
        return self.payslip.employee.account.fullname

    def clean(self):
        """But why will montly tax *12 not equal yearly tax???? make i just check sha and raise error"""
        if self.tax_amount_yearly != self.tax_amount_monthly * 12:
            raise CustomValidationException({"message": "Yearly tax must be 12 times the monthly tax."})


class Rate(models.Model):
    official_rate = models.FloatField()
    parallel_rate = models.FloatField()
    created = models.DateField(default=timezone.now)
    updated = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Official: {self.official_rate}, Parallel: {self.parallel_rate}"

    def clean(self):
        """Just to be save and prevent double rate existence in a month....make wahala no start oooo"""
        today = timezone.now().date()
        if Rate.objects.filter(created__year = today.year, created__month=today.month).exists():
            raise CustomValidationException({"message": "Rate pulled for the month already"}, 400)
        return super().clean()
    

class Debt(models.Model):
    DEBT_STATUS = (("active", "Active"), ("inactive", "Inactive"))
    payslips = models.ManyToManyField(Payslip, related_name='payslip_debt', blank=True)
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="employee_debt")
    total_owned = models.FloatField()
    paid_so_far = models.FloatField(default=0.0)
    percentage_deduction = models.FloatField(default=15.0, help_text="this is the percentage to remove from employee's monthly pay")
    balance = models.FloatField()
    status = models.CharField(max_length=20, choices=DEBT_STATUS, default="active")
    purpose = models.TextField()
    created = models.DateField(default=timezone.now)
    updated = models.DateField(default=timezone.now)
    last_deducted = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.employee.account.fullname
    
    # def clean(self):
    #     # why will an employee has multiple debts running ---- county hard na


