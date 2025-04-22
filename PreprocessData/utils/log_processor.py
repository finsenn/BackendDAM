# yourapp/utils/log_processor.py
import pandas as pd
import re
import csv
import os

from datetime import datetime
from PreprocessData.models import LogEntry, ImportedFile # Import your model


input_file = '../../CSVDAM/DAM_LOG_26Feb2025.csv'


def process_logs():
    
    output_dir = '../../CSVDAM/output'

    if not os.path.exists(input_file):
        return "❌ log.csv not found."

    df = pd.read_csv(input_file)
    df['Timestamp'] = pd.to_datetime(df['Time Group - 1 Minute'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
    df['Date'] = df['Timestamp'].dt.date
    df['Affected Rows'] = pd.to_numeric(df['Affected Rows'], errors='coerce').fillna(0).astype(int)

    if not os.path.exists(output_dir):
        return f"❌ The directory '{output_dir}' does not exist. Please create it manually."

    # Total queries per day
    total_queries_per_day = df.groupby('Date').size().reset_index(name='Total Queries')
    total_queries_per_day.to_csv(f'{output_dir}/total_queries_per_day.csv', index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"')

    # Total queries per user per day
    total_queries_user_day = df.groupby(['Date', 'User']).size().reset_index(name='Total Queries')
    total_queries_user_day.to_csv(f'{output_dir}/total_queries_user_day.csv', index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"')

    # Total affected rows
    total_affected_rows = df['Affected Rows'].sum()
    pd.DataFrame([{"Total Affected Rows": total_affected_rows}]).to_csv(f'{output_dir}/total_affected_rows.csv', index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"')

    # Affected rows per user
    affected_rows_per_user = df.groupby('User')['Affected Rows'].sum().reset_index(name='Total Affected Rows')
    affected_rows_per_user.to_csv(f'{output_dir}/affected_rows_per_user.csv', index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"')

    # Suspicious queries
    suspicious_keywords = [
        'truncate',
        'drop',
        'delete',
        'xp_cmdshell',
        'sp_executesql',
        'insert bulk',
        'with\\(nolock\\)'
    ]

    def check_suspicious(query):
        if pd.isna(query):
            return False
        return any(re.search(pattern, query, re.IGNORECASE) for pattern in suspicious_keywords)

    df['IsSuspicious'] = df['Query'].apply(check_suspicious)
    suspicious_queries = df[df['IsSuspicious']].copy()
    suspicious_queries[['Timestamp', 'User', 'Query']].to_csv(f'{output_dir}/suspicious_queries.csv', index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"')

    return f"✅ All CSVs exported to the '{output_dir}' directory!"



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

        df['Timestamp'] = pd.to_datetime(df['Time Group - 1 Minute'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
        df['Affected Rows'] = pd.to_numeric(df['Affected Rows'], errors='coerce').fillna(0).astype(int)
        df['Response Size'] = pd.to_numeric(df['Response Size'], errors='coerce').fillna(0).astype(int)

        imported_file = ImportedFile.objects.create(filename=os.path.basename(input_file))

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

        return {
            'status': 'success',
            'message': f"✅ {inserted_count} rows inserted into database",
            'inserted_rows': inserted_count,
            'http_code': 200,
            'api_code': 'IMPORT_SUCCESS'
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f"❌ Import failed: {str(e)}",
            'inserted_rows': 0,
            'http_code': 500,
            'api_code': 'IMPORT_EXCEPTION'
        }
