from rest_framework import status
from rest_framework.exceptions import APIException


class DatesNotAvailable(APIException):
    """
    raise exception when any of the dates on the new reservation overlaps with existing reservations on a given house
    """

    status_code = status.HTTP_406_NOT_ACCEPTABLE

    def __init__(self, days, message=None):
        self.days = days
        if message is None:
            message = (
                f"There is already a reservation with at least one day that overlaps with your selection: {self.days}"
            )

        super().__init__(message)
