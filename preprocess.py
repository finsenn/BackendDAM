import pandas as pd
import re
import csv
import os  # For directory management

# Sumber log
df = pd.read_csv('log.csv')

# Parse datetime
df['Timestamp'] = pd.to_datetime(df['Time Group - 1 Minute'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
df['Date'] = df['Timestamp'].dt.date

# Convert 'Affected Rows' to numeric, filling NaN with 0 and converting to integer
df['Affected Rows'] = pd.to_numeric(df['Affected Rows'], errors='coerce').fillna(0).astype(int)

# Directory to save files
output_dir = 'output'

# Check if the directory exists
if not os.path.exists(output_dir):
    print(f"❌ The directory '{output_dir}' does not exist. Please create it manually.")
else:
    # -------------------------
    # 1. Total queries per day
    # -------------------------
    total_queries_per_day = df.groupby('Date').size().reset_index(name='Total Queries')
    total_queries_per_day.to_csv(f'{output_dir}/total_queries_per_day.csv', index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"')

    # -------------------------------------
    # 2. Total queries per user per day
    # -------------------------------------
    total_queries_user_day = df.groupby(['Date', 'User']).size().reset_index(name='Total Queries')
    total_queries_user_day.to_csv(f'{output_dir}/total_queries_user_day.csv', index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"')

    # ------------------------------
    # 3. Total affected rows overall
    # ------------------------------
    total_affected_rows = df['Affected Rows'].sum()
    pd.DataFrame([{"Total Affected Rows": total_affected_rows}]).to_csv(f'{output_dir}/total_affected_rows.csv', index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"')

    # -------------------------------------
    # 4. Total affected rows per user
    # -------------------------------------
    affected_rows_per_user = df.groupby('User')['Affected Rows'].sum().reset_index(name='Total Affected Rows')
    affected_rows_per_user.to_csv(f'{output_dir}/affected_rows_per_user.csv', index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"')

    # ----------------------------------------------
    # 5. Suspicious queries and what they contain
    # ----------------------------------------------
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

    # For suspicious queries, ensure proper quoting
    suspicious_queries[['Timestamp', 'User', 'Query']].to_csv(f'{output_dir}/suspicious_queries.csv', index=False, quoting=csv.QUOTE_MINIMAL, quotechar='"')

    print(f"✅ All CSVs exported to the '{output_dir}' directory!")
