# yourapp/utils/log_processor.py
import pandas as pd
import re
import csv
import os

from datetime import datetime
from PreprocessData.models import (
    LogEntry,
    ImportedFile,
    TotalQueriesPerDay,
    TotalQueriesPerUserDay,
    TotalAffectedRows,
    AffectedRowsPerUser,
    SuspiciousQuery,
    HourlyQueryVolume,
    SecurityEvent,
    DDLActivity,
    DMLActivity,
)

input_file = './CSVDAM/input.csv'


def process_logs(imported_file):
    output_dir = './CSVDAM'
    print("PROCESS LOG FUNCTION CALLED for file ID", imported_file.id)

    if not os.path.exists(input_file):
        return "❌ input.csv not found."

    df = pd.read_csv(input_file)
    df['Timestamp'] = pd.to_datetime(
        df['Time Group - 1 Minute'],
        format='%m/%d/%Y %I:%M:%S %p',
        errors='coerce'
    )
    df['Date'] = df['Timestamp'].dt.date
    df['Affected Rows'] = (
        pd.to_numeric(df['Affected Rows'], errors='coerce')
        .fillna(0)
        .astype(int)
    )

    if not os.path.exists(output_dir):
        return f"❌ The directory '{output_dir}' does not exist. Please create it manually."

    # classify query types
    def classify_query(q):
        if pd.isna(q):
            return 'UNKNOWN'
        ql = q.lower()
        if 'select' in ql:
            return 'SELECT'
        elif 'insert' in ql:
            return 'INSERT'
        elif 'truncate' in ql:
            return 'TRUNCATE'
        elif 'update' in ql:
            return 'UPDATE'
        elif 'delete' in ql:
            return 'DELETE'
        elif 'drop' in ql:
            return 'DROP'
        return 'OTHER'

    df['Query Type'] = df['Query'].apply(classify_query)

    # prepare summaries
    total_queries_per_day = (
        df.groupby('Date')
        .size()
        .reset_index(name='Total Queries')
    )
    total_queries_user_day = (
        df.groupby(['Date', 'User'])
        .size()
        .reset_index(name='Total Queries')
    )
    total_affected_rows = df['Affected Rows'].sum()
    affected_rows_per_user = (
        df.groupby(['Date', 'User'])['Affected Rows']
        .sum()
        .reset_index(name='Total Affected Rows')
    )
    suspicious_keywords = [
        'truncate','drop','delete','xp_cmdshell',
        'sp_executesql','insert bulk','with\(nolock\)'
    ]
    df['IsSuspicious'] = df['Query'].apply(
        lambda q: any(
            re.search(pat, str(q), re.IGNORECASE)
            for pat in suspicious_keywords
        )
    )
    suspicious_queries = df[df['IsSuspicious']]
    df['Hour'] = df['Timestamp'].dt.hour
    hourly_query_volume = (
        df.groupby(['Date', 'Hour'])
        .size()
        .reset_index(name='Query Count')
    )

    # Security Events
    security_keywords = {
        'password change': ['alter user', 'set password'],
        'failed logon': ['failed login'],
        'role creation': ['create role'],
        'role deletion': ['drop role'],
        'user creation': ['create user'],
        'revoke permissions': ['revoke'],
        'granted permission': ['grant'],
        'shutdown': ['shutdown']
    }

    def classify_security_event(q):
        ql = q.lower() if pd.notna(q) else ''
        for event_type, patterns in security_keywords.items():
            if any(pat in ql for pat in patterns):
                return event_type
        return None

    df['Security Event Type'] = df['Query'].apply(classify_security_event)
    security_events = df[df['Security Event Type'].notna()]

        # Extract object/table name from query as best effort
    def extract_object_name(query):
        if pd.isna(query):
            return None
        match = re.search(r'\b(from|into|update|table|join|delete\s+from|truncate\s+table|create\s+table|drop\s+table)\s+([`"\[]?\w+[`"\]]?)', query, re.IGNORECASE)
        if match:
            return match.group(2).strip('`"[]')
        return None

    df['Object Name'] = df['Query'].apply(extract_object_name)


        # Define the DML and DDL types
    dml_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE']
    ddl_types = ['CREATE', 'ALTER', 'DROP']

    # Filter the DataFrame
    dml_activities = df[df['Query Type'].isin(dml_types)]
    ddl_activities = df[df['Query Type'].isin(ddl_types)]

    dml_summary = (
    dml_activities
    .groupby(['Date', 'User', 'Query Type', 'Object Name'])
    .size()
    .reset_index(name='Count')
    )

    ddl_summary = (
    ddl_activities
    .groupby(['Date', 'User', 'Query Type', 'Object Name'])
    .size()
    .reset_index(name='Count')
    )

    # remove old records for this file
    TotalQueriesPerDay.objects.filter(imported_file=imported_file).delete()
    TotalQueriesPerUserDay.objects.filter(imported_file=imported_file).delete()
    TotalAffectedRows.objects.filter(imported_file=imported_file).delete()
    AffectedRowsPerUser.objects.filter(imported_file=imported_file).delete()
    SuspiciousQuery.objects.filter(imported_file=imported_file).delete()
    HourlyQueryVolume.objects.filter(imported_file=imported_file).delete()
    SecurityEvent.objects.filter(imported_file=imported_file).delete()
    DDLActivity.objects.filter(imported_file=imported_file).delete()
    DMLActivity.objects.filter(imported_file=imported_file).delete()

    # insert new summaries with FK
    TotalQueriesPerDay.objects.bulk_create([
        TotalQueriesPerDay(
            imported_file=imported_file,
            date=row['Date'],
            total_queries=row['Total Queries']
        )
        for _, row in total_queries_per_day.iterrows()
    ])
    TotalQueriesPerUserDay.objects.bulk_create([
        TotalQueriesPerUserDay(
            imported_file=imported_file,
            date=row['Date'],
            user=row['User'],
            total_queries=row['Total Queries']
        )
        for _, row in total_queries_user_day.iterrows()
    ])
    for date in total_queries_per_day['Date'].unique():
        TotalAffectedRows.objects.create(
            imported_file=imported_file,
            date=date,
            total_affected_rows=total_affected_rows
        )
    AffectedRowsPerUser.objects.bulk_create([
        AffectedRowsPerUser(
            imported_file=imported_file,
            date=row['Date'],
            user=row['User'],
            total_affected_rows=row['Total Affected Rows']
        )
        for _, row in affected_rows_per_user.iterrows()
    ])
    SuspiciousQuery.objects.bulk_create([
        SuspiciousQuery(
            imported_file=imported_file,
            timestamp=row['Timestamp'],
            date=row['Timestamp'].date(),
            user=row['User'],
            query=row['Query']
        )
        for _, row in suspicious_queries.iterrows()
    ])
    HourlyQueryVolume.objects.bulk_create([
        HourlyQueryVolume(
            imported_file=imported_file,
            date=row['Date'],
            hour=row['Hour'],
            query_count=row['Query Count']
        )
        for _, row in hourly_query_volume.iterrows()
    ])

    SecurityEvent.objects.bulk_create([
    SecurityEvent(
        imported_file=imported_file,
        timestamp=row['Timestamp'],
        date=row['Timestamp'].date(),
        user=row['User'],
        event_type=row['Security Event Type'],
        details=row['Query']  # using 'Query' as event details
    ) for _, row in security_events.iterrows()
    ])

    
    DDLActivity.objects.bulk_create([
    DDLActivity(
        imported_file=imported_file,
        date=row['Date'],
        user=row['User'],
        ddl_type=row['Query Type'],
        object_name=row.get('Object Name', None),
        count=row['Count']
    ) for _, row in ddl_summary.iterrows()
    ])


   
    DMLActivity.objects.bulk_create([
    DMLActivity(
        imported_file=imported_file,
        date=row['Date'],
        user=row['User'],
        dml_type=row['Query Type'],
        table_name=row.get('Object Name', None),
        count=row['Count']
    ) for _, row in dml_summary.iterrows()
    ])

   

    return f"✅ Data processed for file ID {imported_file.id}!"


def import_logs_to_db():
    if not os.path.exists(input_file):
        return {
            'status': 'error',
            'message': f"❌ File {input_file} not found",
            'inserted_rows': 0,
            'http_code': 404,
            'api_code': 'IMPORT_FILE_NOT_FOUND'
        }
    try:
        df = pd.read_csv(input_file)
        df['Timestamp'] = pd.to_datetime(
            df['Time Group - 1 Minute'],
            format='%m/%d/%Y %I:%M:%S %p',
            errors='coerce'
        )
        df['Affected Rows'] = pd.to_numeric(
            df['Affected Rows'], errors='coerce'
        ).fillna(0).astype(int)
        df['Response Size'] = pd.to_numeric(
            df['Response Size'], errors='coerce'
        ).fillna(0).astype(int)

        imported_file = ImportedFile.objects.create(
            filename=os.path.basename(input_file)
        )

        inserted_count = 0
        for _, row in df.iterrows():
            LogEntry.objects.create(
                imported_file=imported_file,
                timestamp=row['Timestamp'],
                user=row['User'],
                event_type=row.get('Event Type', ''),
                object_name=row.get('Object', ''),
                affected_rows=row['Affected Rows'],
                response_size=row['Response Size'],
                query=row.get('Query', ''),
            )
            inserted_count += 1

        # now pass the created file into processing
        process_logs(imported_file)

        # archive the input file
        archive_dir = './CSVDAM/archive'
        os.makedirs(archive_dir, exist_ok=True)
        file_date = pd.to_datetime(df['Time Group - 1 Minute'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce').dropna().min()
        timestamp_str = file_date.strftime('%Y%m%d_%H%M%S') if not pd.isna(file_date) else datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"input_{timestamp_str}.csv"
        os.rename(input_file, os.path.join(archive_dir, new_name))

        return {
            'status': 'success',
            'message': f"✅ {inserted_count} rows inserted",
            'inserted_rows': inserted_count,
            'http_code': 200,
            'api_code': 'IMPORT_SUCCESS'
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"❌ Import failed: {e}",
            'inserted_rows': 0,
            'http_code': 500,
            'api_code': 'IMPORT_EXCEPTION'
        }
