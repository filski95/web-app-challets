import logging
from datetime import datetime
from functools import wraps as functool_wraps


def communicate_user_creation(for_user=False, log=False):
    def actual_decorator(func):
        """takes function to be decorated as argument"""

        @functool_wraps(func)
        def wrapper(self, *args, **kwargs):
            if for_user:
                f = func(self, *args, **kwargs)
                name = kwargs.get("name")
                surname = kwargs.get("surname")
                email = kwargs.get("email")
                # could be replaced with email or smth / send_email()
                print(f"A user {name} {surname} with {email} has been created")
            if log:
                email = kwargs.get("email")
                logging.basicConfig(filename="accounts/user_creation.log", level=logging.INFO, force=True)
                logging.info(
                    f"A user with emai; {email} has been created on {datetime.strftime(datetime.now(),'%y %b %d')}"
                )
            return f

        return wrapper

    return actual_decorator
