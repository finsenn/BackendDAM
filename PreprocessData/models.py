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
        related_name='total_queries_per_day',
        null=True,
        blank=True
    )
    date = models.DateField(null=True, blank=True)
    total_queries = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('imported_file', 'date')


class TotalQueriesPerUserDay(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        related_name='total_queries_user_day',
        null=True,
        blank=True
    )
    date = models.DateField(null=True, blank=True)
    user = models.CharField(max_length=255, null=True, blank=True)
    total_queries = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('imported_file', 'date', 'user')


class TotalAffectedRows(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        related_name='total_affected_rows',
        null=True,
        blank=True
    )
    date = models.DateField(null=True, blank=True)
    total_affected_rows = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('imported_file', 'date')


class AffectedRowsPerUser(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        related_name='affected_rows_per_user',
        null=True,
        blank=True
    )
    date = models.DateField(null=True, blank=True)
    user = models.CharField(max_length=255, null=True, blank=True)
    total_affected_rows = models.IntegerField(null=True, blank=True)

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
    user = models.CharField(max_length=255, null=True, blank=True)
    query = models.TextField(null=True, blank=True)


class HourlyQueryVolume(models.Model):
    imported_file = models.ForeignKey(
        ImportedFile,
        on_delete=models.CASCADE,
        related_name='hourly_query_volume',
        null=True,
        blank=True
    )
    date = models.DateField(null=True, blank=True)
    hour = models.IntegerField(null=True, blank=True)
    query_count = models.IntegerField(null=True, blank=True)

    class Meta:
        unique_together = ('imported_file', 'date', 'hour')

class SecurityEvent(models.Model):
    imported_file = models.ForeignKey(ImportedFile, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField()
    date = models.DateField()
    user = models.CharField(max_length=255, null=True, blank=True)
    event_type = models.CharField(max_length=100)  # e.g., 'FAILED_LOGIN', 'USER_CREATION'
    details = models.TextField(null=True, blank=True)

class DMLActivity(models.Model):
    imported_file = models.ForeignKey(ImportedFile, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    user = models.CharField(max_length=255)
    dml_type = models.CharField(max_length=50)  # e.g., INSERT, UPDATE, DELETE, SELECT
    table_name = models.CharField(max_length=255, null=True, blank=True)
    query = models.TextField(null=True, blank=True)

class DDLActivity(models.Model):
    imported_file = models.ForeignKey(ImportedFile, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField()
    user = models.CharField(max_length=255)
    ddl_type = models.CharField(max_length=50)  # CREATE_TABLE, DROP_DB, ALTER_TABLE, etc.
    object_name = models.CharField(max_length=255, null=True, blank=True)
    count = models.IntegerField()
