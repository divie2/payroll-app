from django.contrib import admin
from .models import Employee, LoanRequest, Team, NextOfKin, PayrollStaff, Payslip, Tax, Rate, PayrollStaff, Debt

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ["account", "jira_ticket_id", "base_pay", "status"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name", "lead", "created", "updated"]


@admin.register(NextOfKin)
class NextOfKinAdmin(admin.ModelAdmin):
    list_display = ["employee", "name", "address", "phone"]

@admin.register(PayrollStaff)
class PayrollStaffAdmin(admin.ModelAdmin):
    list_display = ["employee", "status", "created", "updated"]


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    list_display = ["employee", "official_base_pay", "parallel_base_pay", "paid", "pay_date", "created"]


@admin.register(Tax)
class TaxAdmin(admin.ModelAdmin):
    list_display = ["payslip", "tax_amount_monthly", "tax_amount_yearly", "created", "updated"]


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ["official_rate", "parallel_rate", "created", "updated"]

@admin.register(LoanRequest)
class LoanRequestAdmin(admin.ModelAdmin):
    list_display = ["employee", "status", "amount" ,"purpose" ,"created", "updated"]
@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ["employee", 'total_owned', "paid_so_far", "balance", "status"]

