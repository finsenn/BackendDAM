# yourapp/utils/log_processor.py
import pandas as pd
import re
import csv
import os

def process_logs():
    input_file = './CSVDAM/DAM_LOG_26Feb2025.csv'
    output_dir = './CSVDAM/output'

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
