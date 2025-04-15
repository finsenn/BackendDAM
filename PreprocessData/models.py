from django.db import models

class LogEntry(models.Model):
    timestamp = models.DateTimeField(null=True, blank=True)
    user = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100, null=True, blank=True)
    object_name = models.CharField(max_length=255, null=True, blank=True)
    affected_rows = models.IntegerField(default=0)
    response_size = models.IntegerField(default=0)
    query = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.timestamp} - {self.user}'
