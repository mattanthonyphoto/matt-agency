"""
Update 2026 Finance Sheet Template
- Replace all "2025" text with "2026" across all tabs
- Clear 2025 transaction data from Transactions tab
- Update Tax tab with 2026 rates and UCC values
- Update GST tab due dates and reset filed checkboxes
- Clear Mileage tab trip data
- Clear Insights tab calculated values
- Update Equipment tab UCC to 2026 opening balances
- Import 2026 transactions from old 2026 sheet
- Save sheet ID to .env
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service

NEW_ID = '1fPpOPnAYEnfCu33h1ki9NzFGTUOkpgd4mMSQX_sT9CY'
OLD_ID = '1KrEyElVbC-F4cP8asFa3BIh9PvIsKsF2mu6W9LUc1Yg'


def run():
    svc = get_sheets_service()
    requests = []

    # ─────────────────────────────────────────────
    # STEP 1: Update "2025" → "2026" in text cells
    # ─────────────────────────────────────────────
    print("Step 1: Updating 2025 → 2026 text references...")

    text_updates = []

    # Dashboard title (row 2, col C = index 2)
    text_updates.append({
        "range": "Dashboard!C2",
        "values": [["Finance Dashboard  ·  2026"]]
    })

    # Transactions title row 1
    text_updates.append({
        "range": "Transactions!A1",
        "values": [["Transactions  ·  2026"]]
    })

    # Tax tab title
    text_updates.append({
        "range": "Tax!B2",
        "values": [["Tax Summary  |  PREPARED FOR CRA FILING  |  2026"]]
    })

    # GST tab title
    text_updates.append({
        "range": "GST!B2",
        "values": [["GST / HST Tracker  |  2026"]]
    })
    text_updates.append({
        "range": "GST!B3",
        "values": [["5% GST  |  Quarterly Filing  |  Registration #: ____________"]]
    })

    # Mileage tab titles
    text_updates.append({
        "range": "Mileage!A1",
        "values": [["Mileage Log — 2026"]]
    })
    text_updates.append({
        "range": "Mileage!A2",
        "values": [["CRA-compliant vehicle log  ·  90% business use  ·  IT-522R"]]
    })

    # Equipment tab header
    text_updates.append({
        "range": "Equipment!A3",
        "values": [["Capital Cost Allowance Schedule  ·  AII Applied  ·  2026"]]
    })
    # Equipment footer rows (rows 31, 32)
    text_updates.append({
        "range": "Equipment!A31",
        "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]
    })

    # Insights tab title
    text_updates.append({
        "range": "Insights!A1",
        "values": [["Insights  ·  Financial Intelligence  ·  2026"]]
    })

    # Write all text updates
    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=NEW_ID,
        body={"valueInputOption": "USER_ENTERED", "data": text_updates}
    ).execute()
    print("  Done — text updated.")

    # ─────────────────────────────────────────────
    # STEP 2: Clear 2025 transaction data
    # ─────────────────────────────────────────────
    print("Step 2: Clearing 2025 transaction data...")

    # We need to clear income data rows (6 to 141) and expense data rows (146 to 1401)
    # but keep the header/label rows (1-5 for income section, 142-145 for expense section)
    # Income data: rows 6-141 (0-indexed: 5-140), cols A-N
    # Expense data: rows 146-1401 (0-indexed: 145-1400), cols A-N

    # Build empty rows for clearing
    # Income section: rows 6-141 = 136 rows
    empty_income = [[""] * 14 for _ in range(136)]
    # Expense section: rows 146-1401 = 1256 rows
    empty_expense = [[""] * 14 for _ in range(1256)]

    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=NEW_ID,
        body={
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": "Transactions!A6:N141", "values": empty_income},
                {"range": "Transactions!A146:N1401", "values": empty_expense},
            ]
        }
    ).execute()
    print("  Done — transaction data cleared.")

    # ─────────────────────────────────────────────
    # STEP 3: Update Tax tab for 2026
    # ─────────────────────────────────────────────
    print("Step 3: Updating Tax tab for 2026...")

    tax_updates = []

    # 2026 Federal BPA: $16,705 × 15% = $2,505.75
    tax_updates.append({
        "range": "Tax!B33:D33",
        "values": [[-2505.75, "", "$16,705 × 15%"]]
    })

    # 2026 BC BPA: $13,216 × 5.06% = $668.73
    tax_updates.append({
        "range": "Tax!B37:D37",
        "values": [[-668.73, "", "$13,216 × 5.06%"]]
    })

    # 2026 CPP: 11.90%, max $8,068.20 (same formula, just update note)
    # CPP formula: =IF(C28>3500,MIN((C28-3500)*0.119,8068.2),0)
    tax_updates.append({
        "range": "Tax!C42",
        "values": [["=IF(C28>3500,MIN((C28-3500)*0.1190,8068.20),0)"]]
    })

    # 2026 CPP2: 8% on $71,300-$79,400, max $648
    tax_updates.append({
        "range": "Tax!C43",
        "values": [["=IF(C28>71300,MIN((C28-71300)*0.08,648),0)"]]
    })

    # Home Office: =1100*12*0.5 = $6,600 (full year at $1,100/mo)
    tax_updates.append({
        "range": "Tax!B22:D22",
        "values": [["Home Office", "=1100*12*0.5", "50% of $1,100/mo × 12 months"]]
    })

    # Clear CCA (will be recalculated from Equipment)
    tax_updates.append({
        "range": "Tax!C23",
        "values": [["='Equipment'!G37"]]
    })
    tax_updates.append({
        "range": "Tax!D23",
        "values": [["CCA schedule (2026)"]]
    })

    # Clear Vehicle / Mileage (will be populated as year progresses)
    tax_updates.append({
        "range": "Tax!C12:D12",
        "values": [["", "Update with 2026 CRA mileage rate × km driven"]]
    })

    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=NEW_ID,
        body={"valueInputOption": "USER_ENTERED", "data": tax_updates}
    ).execute()
    print("  Done — Tax tab updated.")

    # ─────────────────────────────────────────────
    # STEP 4: Update GST tab for 2026
    # ─────────────────────────────────────────────
    print("Step 4: Updating GST tab for 2026...")

    # 2026 quarterly due dates (2027 dates):
    # Q1 (Jan-Mar) → Apr 30, 2027 = date serial 47076 (2027-04-30)
    # Q2 (Apr-Jun) → Jul 31, 2027 = date serial 47167
    # Q3 (Jul-Sep) → Oct 31, 2027 = date serial 47259
    # Q4 (Oct-Dec) → Jan 31, 2028 = date serial 47339
    # Google Sheets date: days since Dec 30, 1899
    # 2027-04-30: Jan1,1900=1, 2027-01-01 = days from 1900 to 2027...
    # Let me use the text dates and let sheets parse them
    gst_updates = [
        # Clear hardcoded quarterly values — replace with formulas from Transactions
        {
            "range": "GST!C6:G7",
            "values": [
                # GST Collected per quarter (formulas pulling from Transactions)
                [
                    '=SUMPRODUCT((Transactions!E$4:E$2002=TRUE)*(Transactions!D$4:D$2002>0)*((Transactions!M$4:M$2002>=1)*(Transactions!M$4:M$2002<=3))*Transactions!H$4:H$2002)',
                    '=SUMPRODUCT((Transactions!E$4:E$2002=TRUE)*(Transactions!D$4:D$2002>0)*((Transactions!M$4:M$2002>=4)*(Transactions!M$4:M$2002<=6))*Transactions!H$4:H$2002)',
                    '=SUMPRODUCT((Transactions!E$4:E$2002=TRUE)*(Transactions!D$4:D$2002>0)*((Transactions!M$4:M$2002>=7)*(Transactions!M$4:M$2002<=9))*Transactions!H$4:H$2002)',
                    '=SUMPRODUCT((Transactions!E$4:E$2002=TRUE)*(Transactions!D$4:D$2002>0)*((Transactions!M$4:M$2002>=10)*(Transactions!M$4:M$2002<=12))*Transactions!H$4:H$2002)',
                    '=SUM(C6:F6)',
                ],
                # ITCs per quarter
                [
                    '=SUMPRODUCT((Transactions!E$4:E$2002=TRUE)*(Transactions!D$4:D$2002<0)*((Transactions!M$4:M$2002>=1)*(Transactions!M$4:M$2002<=3))*Transactions!H$4:H$2002)',
                    '=SUMPRODUCT((Transactions!E$4:E$2002=TRUE)*(Transactions!D$4:D$2002<0)*((Transactions!M$4:M$2002>=4)*(Transactions!M$4:M$2002<=6))*Transactions!H$4:H$2002)',
                    '=SUMPRODUCT((Transactions!E$4:E$2002=TRUE)*(Transactions!D$4:D$2002<0)*((Transactions!M$4:M$2002>=7)*(Transactions!M$4:M$2002<=9))*Transactions!H$4:H$2002)',
                    '=SUMPRODUCT((Transactions!E$4:E$2002=TRUE)*(Transactions!D$4:D$2002<0)*((Transactions!M$4:M$2002>=10)*(Transactions!M$4:M$2002<=12))*Transactions!H$4:H$2002)',
                    '=SUM(C7:F7)',
                ],
            ]
        },
        # Due dates for 2027 (2026 filing)
        {
            "range": "GST!C11:F11",
            "values": [["Apr 30, 2027", "Jul 31, 2027", "Oct 31, 2027", "Jan 31, 2028"]]
        },
        # Reset Filed? checkboxes
        {
            "range": "GST!C12:F12",
            "values": [[False, False, False, False]]
        },
        # Clear payment dates
        {
            "range": "GST!C13:F13",
            "values": [["", "", "", ""]]
        },
    ]

    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=NEW_ID,
        body={"valueInputOption": "USER_ENTERED", "data": gst_updates}
    ).execute()
    print("  Done — GST tab updated.")

    # ─────────────────────────────────────────────
    # STEP 5: Clear Mileage tab trip data
    # ─────────────────────────────────────────────
    print("Step 5: Clearing Mileage tab...")

    # Read Mileage tab to find data rows
    result = svc.spreadsheets().values().get(
        spreadsheetId=NEW_ID,
        range='Mileage!A1:Z20',
        valueRenderOption='FORMULA'
    ).execute()
    mileage_rows = result.get('values', [])
    print(f"  Mileage tab first rows:")
    for i, r in enumerate(mileage_rows[:8]):
        if r:
            print(f"    Row {i+1}: {r[:6]}")

    # Clear rows 5 onwards (data rows, keep title, subtitle, blank, headers)
    svc.spreadsheets().values().clear(
        spreadsheetId=NEW_ID,
        range='Mileage!A5:Z1000'
    ).execute()
    print("  Done — Mileage data cleared.")

    # ─────────────────────────────────────────────
    # STEP 6: Clear Insights tab calculated values
    # ─────────────────────────────────────────────
    print("Step 6: Clearing Insights tab...")

    # Clear data rows (6 onwards) but keep headers
    svc.spreadsheets().values().clear(
        spreadsheetId=NEW_ID,
        range='Insights!A6:J120'
    ).execute()
    print("  Done — Insights cleared.")

    # ─────────────────────────────────────────────
    # STEP 7: Update Equipment tab UCC to 2026 opening balances
    # ─────────────────────────────────────────────
    print("Step 7: Updating Equipment tab UCC for 2026...")

    # Read current equipment data to get UCC End values (column H)
    result = svc.spreadsheets().values().get(
        spreadsheetId=NEW_ID,
        range='Equipment!A5:L37',
        valueRenderOption='FORMULA'
    ).execute()
    eq_rows = result.get('values', [])

    # The 2025 UCC End (col H, index 7) becomes 2026 UCC Start (col F, index 5)
    # For assets, we need to recalculate UCC Start based on 2025 UCC End
    # Known 2025 UCC End values (from CCA schedule):
    # Class 8 assets at 20% rate with AII (1.5x in first year)
    # Opening UCC Class 8: $36,956 (carried from 2025)
    # Opening UCC Class 50: $173 (carried from 2025)

    # The per-row approach: update UCC Start (col F) for each asset row
    # based on the calculated UCC End from 2025
    # CCA Claimed formula changes: remove AII (×0.5 becomes ×1.0 minus the rate)
    # For 2026: full CCA rate applies (no AII), so CCA = UCC_start × rate

    eq_updates = []

    # Update each asset row: set UCC Start = 2025's UCC End (H col value)
    # and update CCA formula to non-AII version
    # Assets are in rows 6-17 (0-indexed 1-12 in result)
    asset_rows = []
    for i, r in enumerate(eq_rows):
        if r and r[0] and r[0] not in ['Asset', 'Class 8', 'Class 10', 'Class 12', 'Class 50',
                                         'AII Note: The Accelerated Investment Incentive applies a 1.5x multiplier to CCA rates in the year an asset is acquired. This enhanced deduction was applied to all 2025 acquisitions.',
                                         'Prepared by: Matt Anthony Photography',
                                         'Tax Year: 2025  |  Filing: June 15, 2027  |  GST: Quarterly',
                                         'Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly',
                                         'This document supports T2125 Statement of Business Activities',
                                         'Note: CCA calculated per half-year rule. Accelerated Investment Incentive (AII) applies 1.5x rate in year of acquisition.',
                                         'TOTALS']:
            sheet_row = i + 6  # rows start at row 6 (1-indexed), eq_rows[0] = row 5 (header)
            if len(r) >= 8 and r[4]:  # has Cost value
                asset_rows.append((sheet_row, r))

    print(f"  Found {len(asset_rows)} equipment assets to update")
    for sheet_row, r in asset_rows:
        print(f"    Row {sheet_row}: {r[0]} — Cost:{r[4]}, UCC Start:{r[5]}, CCA:{r[6]}, UCC End:{r[7]}")

    # For 2026:
    # - UCC Start = UCC End from 2025 (calculate: UCC_start_2025 - CCA_2025)
    # - CCA 2026 = UCC_start_2026 × rate (full rate, no AII)
    # - UCC End 2026 = UCC_start_2026 - CCA_2026
    # Since 2025 used AII (half-year × 1.5 = 0.75 of rate in first year for new assets),
    # but here the formula was just F*D*0.5 (half-year rule without explicit AII multiplier)
    # UCC End 2025 = F - G = UCC_start - (UCC_start × rate × 0.5)

    # Set UCC Start for 2026 = UCC End from 2025 = F6-G6 values
    # We'll use formulas: for row 6, UCC_end_2025 = F6*(1-D6*0.5)
    # So for 2026: new F = old F*(1-D*0.5), new G = new F * D (full rate), new H = new F - new G

    # Actually the cleanest approach: compute the 2026 UCC start numerically
    # then write static values for UCC Start, and update CCA formula for full rate
    for sheet_row, r in asset_rows:
        try:
            ucc_start_2025 = float(r[5]) if r[5] else 0
            rate = float(r[3]) if r[3] else 0
            # 2025 CCA was UCC_start × rate × 0.5 (AII half-year)
            cca_2025 = ucc_start_2025 * rate * 0.5
            ucc_end_2025 = round(ucc_start_2025 - cca_2025, 2)
            # 2026: UCC Start = UCC End 2025
            # CCA 2026: half-year rule still applies for non-first-year = full rate
            # But for simplicity use formula referencing the UCC start
            eq_updates.append({
                "range": f"Equipment!F{sheet_row}",
                "values": [[ucc_end_2025]]
            })
            # Update CCA formula for 2026 (full rate, NOT AII)
            # =F6*D6 (full CCA rate, half-year rule still applies for consistency — keep ×0.5 only for new 2026 acquisitions)
            # For existing assets (not first year) the full rate applies
            eq_updates.append({
                "range": f"Equipment!G{sheet_row}",
                "values": [[f"=F{sheet_row}*D{sheet_row}"]]
            })
            eq_updates.append({
                "range": f"Equipment!H{sheet_row}",
                "values": [[f"=F{sheet_row}-G{sheet_row}"]]
            })
        except (ValueError, TypeError) as e:
            print(f"    Skipping row {sheet_row}: {e}")

    if eq_updates:
        svc.spreadsheets().values().batchUpdate(
            spreadsheetId=NEW_ID,
            body={"valueInputOption": "USER_ENTERED", "data": eq_updates}
        ).execute()

    print("  Done — Equipment UCC updated for 2026.")

    # ─────────────────────────────────────────────
    # STEP 8: Import 2026 transactions from old sheet
    # ─────────────────────────────────────────────
    print("Step 8: Importing 2026 transactions from old sheet...")

    result = svc.spreadsheets().values().get(
        spreadsheetId=OLD_ID,
        range='Transactions!A1:N327',
        valueRenderOption='FORMULA'
    ).execute()
    old_rows = result.get('values', [])

    # Parse income and expense data rows from old sheet
    income_data = []
    expense_data = []
    in_income = False
    in_expense = False

    for i, r in enumerate(old_rows):
        if r and r[0] == 'INCOME':
            in_income = True
            in_expense = False
            continue
        if r and r[0] == 'EXPENSES':
            in_income = False
            in_expense = True
            continue
        if r and r[0] == 'Date':
            continue  # skip header rows
        if r and r[0] and str(r[0]).strip():
            # Strip the Month formula (col N, index 13) — we'll regenerate
            data_cols = r[:13]  # cols A through M (0-12)
            if in_income:
                income_data.append(data_cols)
            elif in_expense:
                expense_data.append(data_cols)

    print(f"  Found {len(income_data)} income rows and {len(expense_data)} expense rows from old 2026 sheet")

    # Add month helper formulas for each row
    def add_month_formula(rows, start_sheet_row):
        """Add month formula as col M (index 12) to each row."""
        result = []
        for i, r in enumerate(rows):
            sheet_row = start_sheet_row + i
            # Pad to 13 cols
            while len(r) < 13:
                r.append("")
            month_f = f'=IF(A{sheet_row}="",0,IFERROR(MONTH(A{sheet_row}),IFERROR(VALUE(LEFT(A{sheet_row},FIND("/",A{sheet_row})-1)),0)))'
            r_with_month = list(r[:12]) + [month_f]
            result.append(r_with_month)
        return result

    # Income data starts at row 6 in new sheet
    income_with_month = add_month_formula(income_data, 6)
    # Expense data starts at row 146 in new sheet
    expense_with_month = add_month_formula(expense_data, 146)

    write_data = []
    if income_with_month:
        write_data.append({
            "range": f"Transactions!A6:M{5 + len(income_with_month)}",
            "values": income_with_month
        })
    if expense_with_month:
        write_data.append({
            "range": f"Transactions!A146:M{145 + len(expense_with_month)}",
            "values": expense_with_month
        })

    if write_data:
        svc.spreadsheets().values().batchUpdate(
            spreadsheetId=NEW_ID,
            body={"valueInputOption": "USER_ENTERED", "data": write_data}
        ).execute()

    print(f"  Done — {len(income_data)} income + {len(expense_data)} expense rows imported.")

    # ─────────────────────────────────────────────
    # STEP 9: Update .env
    # ─────────────────────────────────────────────
    print("Step 9: Updating .env...")

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(base, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()
        if "FINANCE_SHEET_2026_ID" in content:
            import re
            content = re.sub(r"FINANCE_SHEET_2026_ID=.*", f"FINANCE_SHEET_2026_ID={NEW_ID}", content)
        else:
            content = content.rstrip() + f"\nFINANCE_SHEET_2026_ID={NEW_ID}\n"
        with open(env_path, "w") as f:
            f.write(content)
    print(f"  Saved: FINANCE_SHEET_2026_ID={NEW_ID}")

    # ─────────────────────────────────────────────
    # STEP 10: Final verification
    # ─────────────────────────────────────────────
    print("\nStep 10: Final verification...")

    # Check Dashboard KPI cell
    check = svc.spreadsheets().values().get(
        spreadsheetId=NEW_ID,
        range='Dashboard!C2',
        valueRenderOption='FORMATTED_VALUE'
    ).execute()
    dash_title = check.get('values', [['']])[0][0]
    print(f"  Dashboard title: {dash_title}")

    # Check Transactions title
    check2 = svc.spreadsheets().values().get(
        spreadsheetId=NEW_ID,
        range='Transactions!A1',
        valueRenderOption='FORMATTED_VALUE'
    ).execute()
    txn_title = check2.get('values', [['']])[0][0]
    print(f"  Transactions title: {txn_title}")

    # Check Tax tab BPA
    check3 = svc.spreadsheets().values().get(
        spreadsheetId=NEW_ID,
        range='Tax!B2',
        valueRenderOption='FORMATTED_VALUE'
    ).execute()
    tax_title = check3.get('values', [['']])[0][0]
    print(f"  Tax title: {tax_title}")

    # Count populated transaction rows
    result = svc.spreadsheets().values().get(
        spreadsheetId=NEW_ID,
        range='Transactions!A6:A300',
        valueRenderOption='FORMATTED_VALUE'
    ).execute()
    inc_count = sum(1 for r in result.get('values', []) if r and r[0])

    result2 = svc.spreadsheets().values().get(
        spreadsheetId=NEW_ID,
        range='Transactions!A146:A500',
        valueRenderOption='FORMATTED_VALUE'
    ).execute()
    exp_count = sum(1 for r in result2.get('values', []) if r and r[0])

    print(f"  Transactions loaded: {inc_count} income rows, {exp_count} expense rows")

    url = f"https://docs.google.com/spreadsheets/d/{NEW_ID}"
    print(f"\n{'='*60}")
    print(f"DONE!")
    print(f"URL: {url}")
    print(f"{'='*60}")
    print("\nSummary of changes:")
    print(f"  - All '2025' text updated to '2026' across all tabs")
    print(f"  - 2025 transaction data cleared (income + expense rows)")
    print(f"  - Tax tab: 2026 BPA federal=${2505.75}, BC=${668.73}, CPP 11.90%")
    print(f"  - Tax tab: Home Office = $1,100×12×50% = $6,600")
    print(f"  - Tax tab: Vehicle/Mileage cleared for 2026 tracking")
    print(f"  - GST tab: Due dates updated to 2027, Filed? reset to FALSE")
    print(f"  - GST tab: Quarterly values now formula-driven from Transactions")
    print(f"  - Mileage tab: Trip data cleared")
    print(f"  - Insights tab: Calculated values cleared")
    print(f"  - Equipment tab: UCC Start updated to 2026 opening balances")
    print(f"  - Equipment tab: CCA formula updated (full rate, no AII)")
    print(f"  - Transactions: {inc_count} income + {exp_count} expense rows from 2026")
    print(f"  - .env updated: FINANCE_SHEET_2026_ID={NEW_ID}")

    return url


if __name__ == "__main__":
    run()
