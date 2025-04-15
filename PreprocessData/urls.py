# yourapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('run-log-processing/', views.run_log_processing, name='run_log_processing'),

]
