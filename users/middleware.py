# middlewares/sql_logger.py
from django.db import connection
from django.utils.deprecation import MiddlewareMixin
import time


class SQLQueryLoggerMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()

    def process_response(self, request, response):
        total_time = time.time() - getattr(request, '_start_time', time.time())

        print(f"\n=== SQL Queries for {request.path} ===")
        total_sql_time = 0
        for query in connection.queries:
            sql = query.get("sql")
            duration = float(query.get("time", 0))
            total_sql_time += duration
            print(f"[{duration:.3f}s] {sql}")

        print(f"Total SQL time: {total_sql_time:.3f}s | Total request time: {total_time:.3f}s")
        print(f"Total queries: {len(connection.queries)}\n")

        return response
