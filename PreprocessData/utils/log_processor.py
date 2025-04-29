# yourapp/utils/log_processor.py
import pandas as pd
import re
import csv
import os

from datetime import datetime
from PreprocessData.models import LogEntry, ImportedFile # Import your model

from PreprocessData.models import (
    TotalQueriesPerDay,
    TotalQueriesPerUserDay,
    TotalAffectedRows,
    AffectedRowsPerUser,
    SuspiciousQuery,
    TopObject,
    AvgResponseSizePerUser,
    QueryTypeDistribution
)

input_file = './CSVDAM/input.csv'


def process_logs():
    output_dir = './CSVDAM'
    print("PROCESS LOG FUNCTION CALLED")
    if not os.path.exists(input_file):
        return "❌ input.csv not found."

    df = pd.read_csv(input_file)
    df['Timestamp'] = pd.to_datetime(df['Time Group - 1 Minute'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
    df['Date'] = df['Timestamp'].dt.date
    df['Affected Rows'] = pd.to_numeric(df['Affected Rows'], errors='coerce').fillna(0).astype(int)

    if not os.path.exists(output_dir):
        return f"❌ The directory '{output_dir}' does not exist. Please create it manually."
    
    # Top objects by usage
    top_objects = df.groupby('Object').size().reset_index(name='Access Count').sort_values(by='Access Count', ascending=False).head(10)
    top_objects.to_csv(f'{output_dir}/top_objects.csv', index=False)

    # Avg size
    df['Date'] = df['Timestamp'].dt.date
    avg_size = df.groupby(['Date', 'User'])['Response Size'].mean().reset_index(name='Avg Response Size')
    avg_size.to_csv(f'{output_dir}/avg_response_size_user.csv', index=False)
    
    # query type
    def classify_query(q):
        if pd.isna(q): return 'UNKNOWN'
        q = q.lower()
        if 'select' in q: return 'SELECT'
        elif 'insert' in q: return 'INSERT'
        elif 'truncate' in q: return 'TRUNCATE'
        elif 'update' in q: return 'UPDATE'
        elif 'delete' in q: return 'DELETE'
        elif 'drop' in q: return 'DROP'
        return 'OTHER'
    
    df['Query Type'] = df['Query'].apply(classify_query)
    query_types = df['Query Type'].value_counts().reset_index()
    query_types.columns = ['Query Type', 'Count']
    query_types.to_csv(f'{output_dir}/query_type_distribution.csv', index=False)

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
    affected_rows_per_user = df.groupby(['Date', 'User'])['Affected Rows'].sum().reset_index(name='Total Affected Rows')
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

    # ✅ Insert into the database
    dates = df['Date'].unique()

    # Clean up old records for those dates (avoiding duplicates)
    TotalQueriesPerDay.objects.filter(date__in=dates).delete()
    TotalQueriesPerUserDay.objects.filter(date__in=dates).delete()
    TotalAffectedRows.objects.filter(date__in=dates).delete()
    AffectedRowsPerUser.objects.filter(date__in=dates).delete()
    SuspiciousQuery.objects.filter(date__in=dates).delete()

    # Insert Total Queries Per Day
    TotalQueriesPerDay.objects.bulk_create([
        TotalQueriesPerDay(date=row['Date'], total_queries=row['Total Queries'])
        for _, row in total_queries_per_day.iterrows()
    ])

    # Insert Total Queries Per User Per Day
    TotalQueriesPerUserDay.objects.bulk_create([
        TotalQueriesPerUserDay(date=row['Date'], user=row['User'], total_queries=row['Total Queries'])
        for _, row in total_queries_user_day.iterrows()
    ])

    # Insert Total Affected Rows (assuming it applies to all dates equally)
    for date in dates:
        TotalAffectedRows.objects.create(date=date, total_affected_rows=total_affected_rows)

    # Insert Affected Rows Per User
    AffectedRowsPerUser.objects.bulk_create([
        AffectedRowsPerUser(date=row['Date'], user=row['User'], total_affected_rows=row['Total Affected Rows'])
        for _, row in affected_rows_per_user.iterrows()
    ])

    # Insert Suspicious Queries
    SuspiciousQuery.objects.bulk_create([
        SuspiciousQuery(
            timestamp=row['Timestamp'],
            date=row['Timestamp'].date(),
            user=row['User'],
            query=row['Query']
        )
        for _, row in suspicious_queries.iterrows()
    ])

   
    #delete the csv after inserted to query
    generated_files = [
        'total_queries_per_day.csv',
        'total_queries_user_day.csv',
        'total_affected_rows.csv',
        'affected_rows_per_user.csv',
        'suspicious_queries.csv',
        'top_objects.csv',
        'avg_response_size_user.csv',
        'query_type_distribution.csv',


    ]

    for file_name in generated_files:
        try:
            os.remove(os.path.join(output_dir, file_name))
        except Exception as e:
            print(f"⚠️ Failed to delete {file_name}: {e}")


    return f"✅ All CSVs exported and data inserted into the database for {len(dates)} day(s)!"


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
        

        process_result = process_logs()
        print(f"[process_logs] result: {process_result}")


        # ✅ Move and rename the input_file to an archive folder (after all insertions)
        archive_dir = './CSVDAM/archive'
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)

        df['Date'] = df['Timestamp'].dt.date
        dates = df['Date'].unique()
        new_filename = f"input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        archived_path = os.path.join(archive_dir, new_filename)

        try:
            os.rename(input_file, archived_path)
        except Exception as e:
            print(f"⚠️ Failed to move and rename input file: {e}")

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
