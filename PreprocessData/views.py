from django.shortcuts import render
from .utils.log_processor import process_logs
from .utils.log_processor import import_logs_to_db
from .utils.api_response import api_response
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
import os
from django.shortcuts import render, redirect, get_object_or_404
from .models import ImportedFile

def run_log_processing(request):
    result = process_logs
    return HttpResponse(result)
# Create your views here.
#a


def insert_db(request):
    result = import_logs_to_db()

    return api_response(
        status=result.get('status'),
        message=result.get('message'),
        data={'inserted_rows': result.get('inserted_rows', 0)},
        http_code=result.get('http_code', 500),
        api_code=result.get('api_code', '')
    )

def delete_page(request):
    files = ImportedFile.objects.all().order_by('-imported_at')
    return render(request, 'delete_interface.html', {'files': files})

def delete_file_data(request, file_id):
    file = get_object_or_404(ImportedFile, id=file_id)
    file.logs.all().delete()
    file.delete()
    return redirect('delete_page')