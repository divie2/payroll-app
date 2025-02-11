from django.contrib.auth.tokens import PasswordResetTokenGenerator
from datetime import datetime, timedelta

class ExpiringPasswordResetTokenGenerator(PasswordResetTokenGenerator):

    def check_token(self, user, token, expiry_time=3600):
        """
        Check if the token is valid and within the expiry time.
        - `expiry_time`: time in seconds (default is 3600 seconds = 1 hour).
        """
    
        if not super().check_token(user, token):
            return False


        # Extract the timestamp from the token
        try:
            timestamp = int(token.split("-")[-1])
            current_time = int(datetime.now().timestamp())
            print(timestamp, current_time)
            return (current_time - timestamp) <= expiry_time
        except Exception:
            return False
