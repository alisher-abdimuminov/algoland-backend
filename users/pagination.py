import json
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from utils.secrets import encode


class UsersPagination(PageNumberPagination):
    def get_paginated_response(self, data):
        print(data)
        data = {
            "page": {
                "pages": self.page.paginator.num_pages,
                "number": self.page.number,
                "previous": self.page.previous_page_number() if self.page.has_previous() else None,
                "next": self.page.next_page_number() if self.page.has_next() else None,
                "search": self.request.query_params.get("search", ""),
            },
            "users": data,
        }
        return Response({
            "status": "success",
            "code": "users_001",
            "data": encode(json.dumps(data)),
        })
