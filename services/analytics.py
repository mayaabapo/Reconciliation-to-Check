import pandas as pd


# -----------------------
# FILTER STATUS
# -----------------------
def filter_status(df):
    return df[
        df['status']
        .astype(str)
        .str.lower()
        .str.contains('lowerpaid|notpaid', regex=True)
    ]


# -----------------------
# CLEAN DATA
# -----------------------
def clean_df(df):
    return df.fillna('').astype(str).apply(lambda x: x.str.strip().str.lower())


# -----------------------
# VALIDATE OFFICE
# -----------------------
def validate_office(last_df, current_df, expected_office):
    if str(last_df['office'].iloc[0]).strip().upper() != expected_office:
        raise ValueError("Last file not for selected destination")

    if str(current_df['office'].iloc[0]).strip().upper() != expected_office:
        raise ValueError("Current file not for selected destination")


# -----------------------
# BOOKING STATS
# -----------------------
def compute_booking_stats(last_df, current_df):
    last_count = len(last_df)
    current_count = len(current_df)
    difference = current_count - last_count

    status = "No change"
    if difference < 0:
        status = "Improved"
    elif difference > 0:
        status = "Declined"

    return last_count, current_count, difference, status


# -----------------------
# NEW + EXISTING ROWS
# -----------------------
def compute_new_existing(last_df, current_df):

    # IMPORTANT: do NOT clean, do not convert types, do not modify values
    comparison = current_df.merge(
        last_df,
        how='left',
        indicator=True
    )

    new_rows = comparison[comparison['_merge'] == 'left_only'].drop(columns=['_merge'])
    existing_rows = comparison[comparison['_merge'] == 'both'].drop(columns=['_merge'])

    return new_rows, existing_rows


# -----------------------
# SERVICE BREAKDOWN
# -----------------------
def service_breakdown(df):
    if 'service type' not in df.columns:
        return ""

    return ", ".join(
        f"{k}: {v}"
        for k, v in df['service type'].value_counts().items()
    )


# -----------------------
# TOP CLIENTS
# -----------------------
def compute_top_clients(current_df):

    if not all(x in current_df.columns for x in ['client', 'client name', 'service type']):
        return []

    grouped = current_df.groupby('client name').agg({
        'client': lambda x: ' / '.join(sorted(x.unique())),
        'client name': 'first'
    }).reset_index(drop=True)

    grouped['count'] = current_df.groupby('client name').size().values

    grouped = grouped.sort_values(
        by=['count', 'client name'],
        ascending=[False, True]
    )

    service_grouped = current_df.groupby(
        ['client name', 'service type']
    ).size().unstack(fill_value=0)

    top_clients = []

    for _, row in grouped.iterrows():
        cname = row['client name']

        breakdown = ""
        if cname in service_grouped.index:
            services = service_grouped.loc[cname]
            services = services[services > 0].sort_values(ascending=False)
            breakdown = " – ".join([f"{s} ({c})" for s, c in services.items()])

        top_clients.append({
            "client_code": row['client'],
            "client_name": cname,
            "count": row['count'],
            "service_breakdown": breakdown
        })

    return top_clients


# -----------------------
# MAIN REPORT
# -----------------------
def build_report(last_df, current_df, expected_office):

    last_df = filter_status(last_df)
    current_df = filter_status(current_df)

    validate_office(last_df, current_df, expected_office)

    last_clean = clean_df(last_df)
    current_clean = clean_df(current_df)

    last_count, current_count, difference, status = compute_booking_stats(last_df, current_df)

    new_rows, existing_rows = compute_new_existing(last_clean, current_clean)

    top_clients = compute_top_clients(current_df)

    return {
        "last": last_count,
        "current": current_count,
        "difference": difference,
        "status": status,

        "new_bookings": len(new_rows),
        "existing_bookings": len(existing_rows),

        "new_rows": new_rows,
        "existing_rows": existing_rows,

        "top_clients": top_clients,
        "last_breakdown": service_breakdown(last_df),
        "current_breakdown": service_breakdown(current_df),
    }