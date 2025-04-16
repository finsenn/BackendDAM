from django.shortcuts import render
from .utils.log_processor import process_logs
from .utils.log_processor import import_logs_to_db
from django.http import HttpResponse
import os

def run_log_processing(request):
    result = process_logs
    return HttpResponse(result)
# Create your views here.

def insert_db(request):
    result = import_logs_to_db()
    return HttpResponse(result)
