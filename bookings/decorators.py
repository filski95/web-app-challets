from functools import wraps as functool_wraps

from django.conf import settings

from bookings.utils import my_date


class LoggingContextManager:
    def __init__(self) -> None:
        self.file = settings.MEDIA_ROOT + "/run_updates.txt"
        self.file_obj = None  # None until __enter__ kicks in

    def logging(self, text):
        self.file_obj.write(f"{text} [{my_date.today()}] \n")

    def __enter__(self):
        self.file_obj = open(self.file, mode="a")
        return self

    def __exit__(self, *args, **kwargs):
        if self.file_obj:
            self.file_obj.close()


def customer_profile_update_decorator(log=False):
    def actual_decorator(func):
        """takes function to be decorated as argument"""
        if log is False:
            return func

        @functool_wraps(func)
        def wrapper(*args, **kwargs):

            profile, hierarchy = args

            profile_status = profile.status
            f = func(*args)
            profile.refresh_from_db()
            update_status = profile.status

            with LoggingContextManager() as log:
                log.logging(
                    f"Profile: {profile}, Initial status: {profile_status}, end status: {update_status}, total visits {profile.total_visits}"
                )

            return f

        return wrapper

    return actual_decorator


class UpdateReservationDecorator:
    def __init__(self, func) -> None:
        self.func = func
        self.loop = 0

    def __call__(self, *args, **kwargs):
        self.loop += 1
        reservations, hierarchy = args

        with LoggingContextManager() as log:
            for r in reservations:
                log.logging(f"Loop {self.loop} {my_date.today()},Reservation {r}, status: {r.status}")
        f = self.func(*args, **kwargs)

        with LoggingContextManager() as log:
            for r in reservations:
                log.logging(f"Loop {self.loop} of {my_date.today()},Reservation {r}, status: {r.status}")
