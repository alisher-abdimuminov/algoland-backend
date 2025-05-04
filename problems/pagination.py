import json
import time
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from utils.secrets import encode


class ProblemsPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        data = {
            "page": {
                "pages": self.page.paginator.num_pages,
                "number": self.page.number,
                "previous": self.page.previous_page_number() if self.page.has_previous() else None,
                "next": self.page.next_page_number() if self.page.has_next() else None,
                "search": self.request.query_params.get("search", ""),
            },
            "problems": data,
        }
        return Response({
            "status": "success",
            "code": "problems_001",
            "data": encode(json.dumps(data)),
        })


class AttemptsPagination(PageNumberPagination):
    page_size = 10
    def get_paginated_response(self, data):
        # time.sleep(5)
        data = {
            "page": {
                "pages": self.page.paginator.num_pages,
                "number": self.page.number,
                "previous": self.page.previous_page_number() if self.page.has_previous() else None,
                "next": self.page.next_page_number() if self.page.has_next() else None,
                "search": self.request.query_params.get("search", ""),
            },
            "attempts": data,
        }
        return Response({
            "status": "success",
            "code": "attempts_001",
            "data": encode(json.dumps(data)),
        })
