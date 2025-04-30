from django.db import models

class ImportedFile(models.Model):
    filename = models.CharField(max_length=255)
    imported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename


class LogEntry(models.Model):
    imported_file = models.ForeignKey(ImportedFile, on_delete=models.CASCADE, null=True, blank=True,related_name='logs')
    timestamp = models.DateTimeField(null=True, blank=True)  # ✅ Add this line
    user = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100, null=True, blank=True)
    object_name = models.CharField(max_length=255, null=True, blank=True)
    affected_rows = models.IntegerField(default=0)
    response_size = models.IntegerField(default=0)
    query = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.timestamp} - {self.user}'
    
class TotalQueriesPerDay(models.Model):
    date = models.DateField(unique=True, null=True, blank=True)
    total_queries = models.IntegerField()
    

class TotalQueriesPerUserDay(models.Model):
    date = models.DateField(unique=True, null=True, blank=True)
    user = models.CharField(max_length=255)
    total_queries = models.IntegerField(default=0)
    

class TotalAffectedRows(models.Model):
    date = models.DateField(unique=True, null=True, blank=True)
    total_affected_rows = models.IntegerField(default=0)

class AffectedRowsPerUser(models.Model):
    date = models.DateField(unique=True, null=True, blank=True)
    user = models.CharField(max_length=255)
    total_affected_rows = models.IntegerField(default=0)

class SuspiciousQuery(models.Model):
    timestamp = models.DateTimeField(default=0)
    date = models.DateField(unique=True, null=True, blank=True)
    user = models.CharField(max_length=255)
    query = models.TextField(default=0)  

class HourlyQueryVolume(models.Model):
    date = models.DateField(unique=True, null=True, blank=True)
    hour = models.IntegerField(default=0)
    query_count = models.IntegerField(default=0)