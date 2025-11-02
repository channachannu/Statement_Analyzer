import pandas as pd

def analyze_statement(df, salary_dates):
    """
    Process the uploaded bank statement and generate cycle-wise summaries.
    """
    #salary_dates = df[df['Narration'].str.contains("Salary", case=False)]['Date'].sort_values().unique()
    salary_dates = pd.to_datetime(salary_dates,format='%Y-%m-%d', errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'],format='%d/%m/%y')
    all_cycles = pd.DataFrame()

    for i in range(len(salary_dates) - 1):
        start, end = salary_dates[i], salary_dates[i + 1]
        tmp = df.loc[(df['Date'] >= start) & (df['Date'] < end)].copy()

        if tmp.empty:
            print(f"Skipping {start.date()} → {end.date()} (no data)")
            continue

        tmp.reset_index(drop=True, inplace=True)
        tmp.columns = ['Date', 'Narration', 'ID', 'value_dt', 'Debit', 'Credit', 'Closing_Balance']
        tmp.sort_values(by=['Date', 'Closing_Balance', 'Debit'], ascending=[True, False, False], inplace=True)

        # --- Threshold calculation ---
        tmp['Prev_Bal'] = tmp['Closing_Balance'].shift(1)
        Threshold = tmp.loc[tmp['Credit'] > 0, 'Closing_Balance'].max()
        tmp['Threshold'] = 0.05 * Threshold
        tmp['Type'] = tmp.apply(
            lambda x: 'Large_Debit' if x['Debit'] > x['Threshold']
            else ('Credit' if x['Credit'] > 0 else 'Small_Debit'),
            axis=1
        )

        # --- Initialize helper DataFrames ---
        db = pd.DataFrame(columns=['Narration', 'Credit', 'Balance', 'Debit']).astype({
            'Narration': 'object', 'Credit': 'float', 'Balance': 'float', 'Debit': 'float'
        })
        sm_db = pd.DataFrame(columns=['Date', 'Debit', 'Closing_Balance']).astype({
            'Date': 'object', 'Debit': 'float', 'Closing_Balance': 'float'
        })

        # --- Loop through transactions ---
        for row in tmp.reset_index().itertuples():
            if row.Index == 0:
                new_row = {
                    'Narration': f"Opening Balance (inc salary) as of {row.Date.date()}",
                    'Credit': row.Credit,
                    'Balance': row.Closing_Balance - row.Credit,
                    'Debit': 0
                }
                db.loc[len(db)] = new_row
            elif row.Index > 0:
                if row.Type == 'Credit':
                    if sm_db['Debit'].sum() > 0:
                        db.loc[len(db)] = {
                            'Narration': f"Combined Small Debits {sm_db['Date'].min()} to {sm_db['Date'].max()}",
                            'Credit': 0,
                            'Balance': sm_db['Closing_Balance'].min(),
                            'Debit': sm_db['Debit'].sum()
                        }
                        sm_db = pd.DataFrame(columns=['Date', 'Debit', 'Closing_Balance'])
                    db.loc[len(db)] = {
                        'Narration': f"Credit on {row.Date.date()}",
                        'Credit': row.Credit,
                        'Balance': row.Closing_Balance,
                        'Debit': 0
                    }

                elif row.Type == 'Small_Debit':
                    sm_db.loc[len(sm_db)] = {
                        'Date': str(row.Date.date()),
                        'Debit': row.Debit,
                        'Closing_Balance': row.Closing_Balance
                    }

                elif row.Type == 'Large_Debit':
                    if sm_db['Debit'].sum() > 0:
                        db.loc[len(db)] = {
                            'Narration': f"Combined Small Debits {sm_db['Date'].min()} to {sm_db['Date'].max()}",
                            'Credit': 0,
                            'Balance': sm_db['Closing_Balance'].min(),
                            'Debit': sm_db['Debit'].sum()
                        }
                        sm_db = pd.DataFrame(columns=['Date', 'Debit', 'Closing_Balance'])
                    db.loc[len(db)] = {
                        'Narration': f"Large Debits on {row.Date.date()}",
                        'Credit': 0,
                        'Balance': row.Closing_Balance,
                        'Debit': row.Debit
                    }

        # --- Add per-cycle summary ---
        opening_balance = db.loc[0, 'Balance'] if not db.empty else 0
        total_credit = db['Credit'].sum()
        total_debit = db['Debit'].sum()
        final_balance = tmp['Closing_Balance'].iloc[-1] if not tmp.empty else 0
        spend_ratio = (total_debit / (total_credit + opening_balance) * 100) if (total_credit + opening_balance) > 0 else 0

        db.loc[len(db)] = {
            'Narration': (
                f"Summary → Period {start.date()} to {end.date()}, "
                f"Opening ₹{opening_balance:,.2f}, Credit ₹{total_credit:,.2f}, "
                f"Debit ₹{total_debit:,.2f}, Closing ₹{final_balance:,.2f}, "
                f"Spending Ratio {spend_ratio:.1f}%"
            ),
            'Credit': total_credit,
            'Balance': final_balance,
            'Debit': total_debit
        }

        db['Cycle'] = f"{start.date()} → {end.date()}"
        all_cycles = pd.concat([all_cycles, db], ignore_index=True)

    return all_cycles
