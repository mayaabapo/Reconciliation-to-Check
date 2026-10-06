from flask import Flask, request, render_template, flash, redirect, url_for, send_file
import pandas as pd
import io

from services.analytics import build_report

app = Flask(__name__)
app.secret_key = 'secret_key_for_flash_messages'

DESTINATIONS = {
    "Dubai": "DXB",
    "Oman": "MCT",
    "Mauritius": "MUS",
    "Qatar": "DOH",
    "Sri Lanka": "LKA"
}

results_store = {}


@app.route('/')
def landing():
    results_store.clear()
    return render_template('landing.html', destinations=DESTINATIONS.keys())


@app.route('/destination/<dest>', methods=['GET', 'POST'])
def destination(dest):

    if dest not in DESTINATIONS:
        flash("Invalid destination")
        return redirect(url_for('landing'))

    results = None
    expected_office = DESTINATIONS[dest]

    if request.method == 'POST':

        last_file = request.files.get('last_week')
        current_file = request.files.get('current_week')

        if not last_file or not last_file.filename.lower().endswith('.xlsx'):
            flash("Last Week file must be .xlsx")
            return redirect(url_for('destination', dest=dest))

        if not current_file or not current_file.filename.lower().endswith('.xlsx'):
            flash("Current Week file must be .xlsx")
            return redirect(url_for('destination', dest=dest))

        try:
            last_df = pd.read_excel(last_file)
            current_df = pd.read_excel(current_file)
        except Exception as e:
            flash(f"Error reading files: {str(e)}")
            return redirect(url_for('destination', dest=dest))

        last_df.columns = [c.strip().lower() for c in last_df.columns]
        current_df.columns = [c.strip().lower() for c in current_df.columns]

        required_cols = ['status', 'office']
        for col in required_cols:
            if col not in last_df.columns or col not in current_df.columns:
                flash(f"Files must contain '{col}' column")
                return redirect(url_for('destination', dest=dest))
        try:
            results = build_report(last_df, current_df, expected_office)
        except Exception as e:
            flash(str(e))
            return redirect(url_for('destination', dest=dest))

        results_store[dest] = results

    if dest in results_store and not results:
        results = results_store[dest]

    return render_template('destination.html', dest=dest, results=results)


# -------------------------
# EXPORT EXCEL ROUTE
# -------------------------
@app.route('/export/<dest>')
def export(dest):

    if dest not in results_store:
        flash("No report available. Please generate first.")
        return redirect(url_for('destination', dest=dest))

    data = results_store[dest]
    new_df = data["new_rows"]
    existing_df = data["existing_rows"]

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        new_df.to_excel(writer, index=False, sheet_name="New Bookings")
        existing_df.to_excel(writer, index=False, sheet_name="Existing Bookings")

    output.seek(0)

    return send_file(
        output,
        download_name=f"{dest}_booking_report.xlsx",
        as_attachment=True
    )


if __name__ == '__main__':
    app.run(debug=True)