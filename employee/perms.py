from employee.models import Employee, PayrollStaff
from rest_framework.permissions import IsAuthenticated
from account.perms import CustomValidationException



        
class IsAuthenticatedAndCRUDEmployee(IsAuthenticated):
    def has_permission(self, request, view):
        # Access the employee_id parameter from the view's kwargs
        employee_id = view.kwargs.get('employee_id')
 
        if employee_id and request.method == 'GET':
            check_bool = request.user.has_perm('employee.view_employee') or self.user_can_view_own_detail(request.user, employee_id)
        elif employee_id and request.method == 'DELETE':
            check_bool = request.user.has_perm('employee.delete_employee')
        else:
            check_bool =  request.user.has_perm('employee.change_employee')
        if not check_bool:
            raise CustomValidationException({"message":"You do not have permission to perform this action"}, 403)
        return True
            

    def user_can_view_own_detail(self, user, employee_id):
        try:
            employee = Employee.objects.get(pk=employee_id)
            return employee.account == user 
        except Employee.DoesNotExist:
            return False
        

class IsAuthenticatedAndOnboardEmployee(IsAuthenticated):
    def has_permission(self, request, view):
        if request.method == 'POST':
            check_bool =  request.user.has_perm('employee.add_employee') and request.user.has_perm('account.add_account') and request.user.has_perm('employee.add_team')
            if not check_bool:
                raise CustomValidationException({"message":"You do not have permission to perform this action"}, 403)
            return True
        raise CustomValidationException({"message":"Method not allowed"}, 405)


class IsPayrollStaff(IsAuthenticated):
    def has_permission(self, request, view):
        check_bool = PayrollStaff.objects.filter(employee__account = request.user, status="active").exists()
        if not check_bool:
            raise CustomValidationException({"message":"You do not have permission to perform this action"}, 403)
        return True
    
class IsAuthenticatedAndChangePayrollStaff(IsAuthenticated):
    def has_permission(self, request, view):
        user = request.user
        check_bool = user.has_perm("employee.add_payrollstaff") and user.has_perm("employee.delete_payrollstaff")
        if not check_bool:
            raise CustomValidationException({"message":"You do not have permission to perform this action"}, 403)
        return True
    