from django.shortcuts import render
from .utils.log_processor import process_logs
from .utils.log_processor import import_logs_to_db
from .utils.api_response import api_response
from django.http import HttpResponse
import os

def run_log_processing(request):
    result = process_logs
    return HttpResponse(result)
# Create your views here.

@require_http_methods(["POST"])
def insert_db(request):
    result = import_logs_to_db()

    return api_response(
        status=result.get('status'),
        message=result.get('message'),
        data={'inserted_rows': result.get('inserted_rows', 0)},
        http_code=result.get('http_code', 500),
        api_code=result.get('api_code', '')
    )
