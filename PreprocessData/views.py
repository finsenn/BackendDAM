from django.shortcuts import render
from utils.log_processor import process_logs
from django.http import HttpResponse

def run_log_processing(request):
    result = process_logs
    return HttpResponse(result)
# Create your views here.
