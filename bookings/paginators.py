# https://stackoverflow.com/questions/44370252/django-rest-framework-how-to-turn-off-on-pagination-in-modelviewset -> viewsets turning off


from rest_framework import pagination
from rest_framework.response import Response


class MyCustomPageNumberPagination(pagination.PageNumberPagination):
    """
    allows client to set page size by using user_page_size parameter -> max_page_size is the upper limit
    page size -> default
    """

    page_size_query_param = "user_page_size"
    page_size = 3
    max_page_size = 25
    last_page_strings = ("last", ("end"))

    def get_paginated_response(self, data):
        return Response(
            {
                "links": {"next": self.get_next_link(), "previous": self.get_previous_link()},
                "count": self.page.paginator.count,
                "results": data,
            }
        )


class MyCustomListOffsetPagination(pagination.LimitOffsetPagination):
    # if page_size set on the project level, limit on the client side becomse optional
    default_limit = 3  # default if not provided by the client
    limit_query_param = "l"
    offset_query_param = "o"
    max_limit = 10  # maximum allowable limit that may be requested by the client.


class MyCustomCursorPaginator(pagination.CursorPagination):
    page_size = 3
    ordering = "edited_on"
