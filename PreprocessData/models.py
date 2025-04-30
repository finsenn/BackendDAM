from django.db import models


class ImportedFile(models.Model):
    filename = models.CharField(max_length=255)
    imported_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename


class LogEntry(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='logs'
    )
    timestamp = models.DateTimeField(null=True, blank=True)
    user = models.CharField(max_length=255)
    event_type = models.CharField(max_length=100, null=True, blank=True)
    object_name = models.CharField(max_length=255, null=True, blank=True)
    affected_rows = models.IntegerField(default=0)
    response_size = models.IntegerField(default=0)
    query = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.timestamp} - {self.user}'


class TotalQueriesPerDay(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        related_name='total_queries_per_day'
    )
    date = models.DateField()
    total_queries = models.IntegerField()

    class Meta:
        unique_together = ('imported_file', 'date')


class TotalQueriesPerUserDay(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        related_name='total_queries_user_day'
    )
    date = models.DateField()
    user = models.CharField(max_length=255)
    total_queries = models.IntegerField()

    class Meta:
        unique_together = ('imported_file', 'date', 'user')


class TotalAffectedRows(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        related_name='total_affected_rows'
    )
    date = models.DateField()
    total_affected_rows = models.IntegerField()

    class Meta:
        unique_together = ('imported_file', 'date')


class AffectedRowsPerUser(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        related_name='affected_rows_per_user'
    )
    date = models.DateField()
    user = models.CharField(max_length=255)
    total_affected_rows = models.IntegerField()

    class Meta:
        unique_together = ('imported_file', 'date', 'user')


class SuspiciousQuery(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        related_name='suspicious_queries',
        null=True,
        blank=True
    )
    timestamp = models.DateTimeField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    user = models.CharField(max_length=255)
    query = models.TextField(null=True, blank=True)


class HourlyQueryVolume(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        related_name='hourly_query_volume'
    )
    date = models.DateField()
    hour = models.IntegerField()
    query_count = models.IntegerField()

    class Meta:
        unique_together = ('imported_file', 'date', 'hour')
