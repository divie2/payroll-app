from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import exception_handler
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from .models import Token



class CustomValidationException(Exception):
    def __init__(self, message: dict, code: int):
        super().__init__(message)
        self.code = code
        self.message = message

    def to_res(self):
        return self.message

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, CustomValidationException):
        custom_response = exc.to_res()
        return Response(custom_response, status=exc.code)
    if isinstance(exc, (TokenError, InvalidToken)):
        response.data = {"message":"Invalid token"}
        
    return response

class IsAuthenticatedAndNotBlacklisted(IsAuthenticated):
    def has_permission(self, request, view) -> bool:
        if request.user.is_authenticated:
            # Now, onto our custom checks
            # 1. Check if the token is blacklisted
            access_token = request.META.get("HTTP_AUTHORIZATION", "").split(" ")
            access_token = access_token[1]  # Assuming it's a Bearer token
            if Token.objects.filter(
                access_token=access_token, is_blacklisted=True
            ).exists():
                raise CustomValidationException({"message":"Invalid token"}, 403)

            return True