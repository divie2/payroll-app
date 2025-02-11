
from django.urls import path
from . import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register('employees', views.EmployeeViewSet, basename='employee')

urlpatterns = [
    path("single-employee/<str:employee_id>", views.EmployeeView.as_view(), name='profile-update'),
    path("filter-employee", views.FilterEmployeeView.as_view(), name='filter-employee'),
    path("upgrade-employee/<str:employee_id>", views.EmployeeUpgradeView.as_view(), name="upgrade_employee"),
    path("payslip/generate-payslips", views.EmployeePaysliplView.as_view(), name = "payslip"),
    path("payslip/generate-payslip/<str:employee_id>", views.EmployeePaysliplView.as_view(), name = "payslip"),
    path("payslip/delete-current-month-payslips", views.EmployeePaysliplView.as_view(), name="delete-current-month-payslips"),
    # List Employees or Get an Employee
    *router.urls,

    path("create_team", views.EmployeeTeamCreate.as_view(), name = "create_team"),
    path("list_teams",views.ListTeam.as_view(),name="list_teams"),

    path("delete_team", views.DeleteTeams.as_view(), name='delete_team'),
    path("update_team/<str:team_id>",views.UpdateTeam.as_view(), name = "update_teams"),

    path("loan_request", views.EmployeeLoanRequest.as_view(), name = "loan_request"),
    path("loan_update/<str:loan_id>", views.EmployeeUpdateLoan.as_view(), name = "loan_update"),
    path("loan_update_admin/<str:loan_id>", views.EmployeeUpdateLoanAdmin.as_view(), name = "loan_update_admin"),
    path("loan_request_list", views.EmployeeLoanRequestList.as_view(), name = "loan_request_list"),

    path("current-month-rate", views.current_month_rate, name = "get_current_month_rate"),
    path('task-status/<str:task_id>', views.TaskStatusView.as_view(), name='task-status'),
    path("set-rate/<str:rate_id>", views.SetRate, name="set-rate"),
    path("taxes/<str:employee_id>", views.get_employee_taxes, name="get_employee_tax"),
    path("taxes", views.get_all_employee_taxes, name="get_employees_tax"),
    path("debts", views.get_employees_debts, name="debts"),
    path("debts/update", views.update_employee_debt, name="update-debt-details")
]
