import pandas as pd

def generate_report(dest, last_file, current_file, DESTINATIONS):
    expected_office = DESTINATIONS[dest]

    # Read files
    last_df = pd.read_excel(last_file)
    current_df = pd.read_excel(current_file)

    # Standardize columns
    last_df.columns = [c.strip().lower() for c in last_df.columns]
    current_df.columns = [c.strip().lower() for c in current_df.columns]

    if 'status' not in last_df.columns or 'status' not in current_df.columns:
        raise ValueError("Both files must contain a 'Status' column.")

    if 'office' not in last_df.columns or 'office' not in current_df.columns:
        raise ValueError("Both files must contain an 'Office' column.")

    # Filter relevant statuses
    def filter_status(df):
        return df[df['status'].astype(str).str.lower().str.contains('lowerpaid|notpaid', regex=True)]

    last_df = filter_status(last_df)
    current_df = filter_status(current_df)

    # Validate office
    last_office = str(last_df['office'].iloc[0]).strip().upper()
    current_office = str(current_df['office'].iloc[0]).strip().upper()
    if last_office != expected_office:
        raise ValueError(f"Last Week file does not belong to {dest}. Expected: {expected_office}")
    if current_office != expected_office:
        raise ValueError(f"Current Week file does not belong to {dest}. Expected: {expected_office}")

    # Counts
    last_count = len(last_df)
    current_count = len(current_df)
    difference = current_count - last_count
    status = "No change" if difference == 0 else ("Improved" if difference < 0 else "Declined")

    # Service breakdown
    def service_breakdown(df):
        if 'service type' not in df.columns:
            return ""
        return ", ".join([f"{k}: {v}" for k, v in df['service type'].value_counts().items()])

    last_breakdown = service_breakdown(last_df)
    current_breakdown = service_breakdown(current_df)

    # New vs existing bookings
    common_cols = list(set(last_df.columns).intersection(set(current_df.columns)))
    last_aligned = last_df[common_cols].astype(str).apply(lambda x: x.str.strip().str.lower())
    current_aligned = current_df[common_cols].astype(str).apply(lambda x: x.str.strip().str.lower())

    comparison = current_aligned.merge(
        last_aligned.drop_duplicates(),
        on=common_cols,
        how='left',
        indicator=True
    )

    new_count = len(comparison[comparison['_merge'] == 'left_only'])
    existing_count = len(comparison[comparison['_merge'] == 'both'])

    # Top clients
    top_clients = []
    if all(x in current_df.columns for x in ['client', 'client name', 'service type']):
        grouped = current_df.groupby('client name').agg({
            'client': lambda x: ' / '.join(sorted(x.unique())),
            'client name':'first'
        }).reset_index(drop=True)
        grouped['count'] = current_df.groupby('client name').size().values
        grouped = grouped.sort_values(by=['count','client name'], ascending=[False, True]).reset_index(drop=True)

        service_grouped = current_df.groupby(['client name','service type']).size().unstack(fill_value=0)
        for _, row in grouped.iterrows():
            client_name = row['client name']
            breakdown = ""
            if client_name in service_grouped.index:
                services = service_grouped.loc[client_name]
                services = services[services > 0].sort_values(ascending=False)
                breakdown = " – ".join([f"{stype} ({count})" for stype, count in services.items()])
            top_clients.append(type('obj',(object,),{
                'client_code': row['client'],
                'client_name': client_name,
                'count': row['count'],
                'service_breakdown': breakdown
            }))

    # Return as object
    return type('obj',(object,),{
        'last': last_count,
        'current': current_count,
        'difference': difference,
        'status': status,
        'top_clients': top_clients,
        'last_breakdown': last_breakdown,
        'current_breakdown': current_breakdown,
        'new_count': new_count,
        'existing_count': existing_count
    })