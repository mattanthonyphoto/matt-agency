"""
Add comprehensive financial intelligence to the 2025 Google Sheet.
Creates Insights tab, updates Business/Personal/Dashboard tabs, adds P&L charts.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_sheets_auth import get_sheets_service

SHEET_ID = '1TyX4sOIo6CxblxjNM9Yft5h5vZO_BGhQjHlgC0uzQtI'

# ── Colors ────────────────────────────────────────────────────────────────────
NAVY       = {"red": 0.153, "green": 0.173, "blue": 0.224}   # #272C39
GRAY_HDR   = {"red": 0.549, "green": 0.573, "blue": 0.612}   # #8C929C
WHITE      = {"red": 1,     "green": 1,     "blue": 1}
ALT_ROW    = {"red": 0.969, "green": 0.973, "blue": 0.980}   # #F7F8FA
BLUE_REV   = {"red": 0.051, "green": 0.278, "blue": 0.631}   # #0D4799
GREEN_PRF  = {"red": 0.149, "green": 0.588, "blue": 0.388}   # #269563
RED_EXP    = {"red": 0.827, "green": 0.184, "blue": 0.184}   # #D32F2F
ORANGE     = {"red": 0.902, "green": 0.494, "blue": 0.133}   # #E67E22
LIGHT_BLUE = {"red": 0.902, "green": 0.941, "blue": 0.996}   # #E6F0FE
LIGHT_GRN  = {"red": 0.898, "green": 0.969, "blue": 0.925}   # #E5F7EC
LIGHT_RED  = {"red": 0.996, "green": 0.898, "blue": 0.898}   # #FEE5E5
LIGHT_ORG  = {"red": 1.0,   "green": 0.953, "blue": 0.882}   # #FFF3E1
YELLOW_FLG = {"red": 1.0,   "green": 0.949, "blue": 0.800}   # #FFF2CC
MID_GRAY   = {"red": 0.851, "green": 0.851, "blue": 0.851}
DARK_BG    = {"red": 0.220, "green": 0.247, "blue": 0.298}   # section bg


def col_idx(letter):
    """A→0, B→1, etc."""
    return ord(letter.upper()) - ord('A')


def cell_ref(col_letter, row_1indexed):
    return {"rowIndex": row_1indexed - 1, "columnIndex": col_idx(col_letter)}


def r(row, col):
    """0-based row, col"""
    return {"rowIndex": row, "columnIndex": col}


def grid_range(sheet_id, start_row, end_row, start_col, end_col):
    return {
        "sheetId": sheet_id,
        "startRowIndex": start_row,
        "endRowIndex": end_row,
        "startColumnIndex": start_col,
        "endColumnIndex": end_col,
    }


def bg(color):
    return {"backgroundColor": color}


def bold_text(size=10, color=None, bold=True):
    fmt = {"bold": bold, "fontSize": size, "fontFamily": "Inter"}
    if color:
        fmt["foregroundColor"] = color
    return fmt


def money_fmt(decimals=0):
    pat = "$#,##0" if decimals == 0 else "$#,##0.00"
    return {"numberFormat": {"type": "CURRENCY", "pattern": pat}}


def pct_fmt():
    return {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}


def repeat_cell(sheet_id, start_row, end_row, start_col, end_col, cell):
    return {
        "repeatCell": {
            "range": grid_range(sheet_id, start_row, end_row, start_col, end_col),
            "cell": cell,
            "fields": ",".join(f"userEnteredFormat.{k}" for k in cell.get("userEnteredFormat", {}).keys()),
        }
    }


def merge(sheet_id, start_row, end_row, start_col, end_col):
    return {
        "mergeCells": {
            "range": grid_range(sheet_id, start_row, end_row, start_col, end_col),
            "mergeType": "MERGE_ALL",
        }
    }


def border_bottom(sheet_id, row_0, col_start, col_end, style="SOLID", width=1, color=None):
    bc = color or MID_GRAY
    return {
        "updateBorders": {
            "range": grid_range(sheet_id, row_0, row_0 + 1, col_start, col_end),
            "bottom": {"style": style, "width": width, "color": bc},
        }
    }


def set_col_width(sheet_id, col, width_px):
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "COLUMNS",
                "startIndex": col,
                "endIndex": col + 1,
            },
            "properties": {"pixelSize": width_px},
            "fields": "pixelSize",
        }
    }


def set_row_height(sheet_id, row_0, height_px):
    return {
        "updateDimensionProperties": {
            "range": {
                "sheetId": sheet_id,
                "dimension": "ROWS",
                "startIndex": row_0,
                "endIndex": row_0 + 1,
            },
            "properties": {"pixelSize": height_px},
            "fields": "pixelSize",
        }
    }


# ── Pre-computed data from transactions ───────────────────────────────────────
MONTHLY_INCOME = {
    1: 5706.84,  2: 8297.98,  3: 5553.54,  4: 14390.37, 5: 14178.06,  6: 4522.05,
    7: 26038.68, 8: 12041.90, 9: 11899.59, 10: 10477.99, 11: 14892.26, 12: 4639.20,
}
MONTHLY_TOTAL_EXP = {
    1: 5332.56,  2: 5797.29,  3: 8719.04,  4: 4389.81,  5: 42763.99,  6: 16112.40,
    7: 17881.84, 8: 41891.55, 9: 6427.98,  10: 13814.53, 11: 14080.01, 12: 9315.45,
}
MONTHLY_BUS_EXP = {
    1: 4415.59,  2: 3994.08,  3: 4130.28,  4: 3423.79,  5: 18731.54,  6: 8294.40,
    7: 4970.65,  8: 37685.11, 9: 4309.28,  10: 6852.16,  11: 3989.39,  12: 5410.67,
}
MONTHLY_PER_EXP = {
    1: 859.84,   2: 1746.10,  3: 4565.89,  4: 962.95,   5: 23905.60,  6: 7759.05,
    7: 12613.25, 8: 4139.67,  9: 1717.16,  10: 6905.32,  11: 9934.71,  12: 3847.73,
}
MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

# Software subscriptions (consolidated)
SOFTWARE_SUBS = [
    ("LeadGenJay",       1326.74),
    ("Instantly.ai",     1302.62),  # combined two plans
    ("Squarespace",       963.14),
    ("Claude/Anthropic",  658.40),
    ("Adobe CC",          530.82),
    ("Adobe (other)",     442.35),
    ("Google (Workspace/Ads)", 426.17),
    ("ChatGPT/OpenAI",    408.77),
    ("Dropbox",           254.33),
    ("GoHighLevel",       167.10),  # from Highlevel
    ("Spotify",           170.52),
    ("Paddle.net",        155.55),
    ("Rule 1",            139.24),
    ("Audible",           120.51),
    ("Buffer",            102.51),
    ("ClickUp",            99.05),
    ("xAI (Grok)",         87.56),
    ("SheetMagic",         84.65),
    ("Soundstripe",       124.02),  # combined
    ("Qwilr",              57.28),
    ("TinyPNG",            56.24),
    ("ManyCh at",          41.46),
    ("Netflix",            42.54),
    ("Epidemic Sound",     24.99),
]
# Sum the software
SOFTWARE_TOTAL = sum(v for _, v in SOFTWARE_SUBS)

# Top 20 expense vendors (excluding income categories, savings)
TOP_VENDORS = [
    ("Camera Canada",          32205.57),
    ("E-Transfer (various)",   36012.72),
    ("Questrade",              26500.00),
    ("Amazon.com",             17517.02),
    ("Bank Loan Payment",      11400.00),
    ("Amazon",                 10269.47),
    ("Affirm Canada",           3461.02),
    ("Cash",                    2250.00),
    ("CRA (tax payments)",      2013.25),
    ("GoHighLevel",             1669.77),
    ("Hector's Your Independent", 1431.95),
    ("LeadGenJay",              1326.74),
    ("Auto (fuel/parking)",     1294.94),
    ("London Drugs",            1269.28),
    ("Instantly.ai",            1118.57),
    ("Squarespace",              963.14),
    ("Trip.com",                 951.40),
    ("Cooperators Insurance",    902.80),
    ("Climb (gear)",             874.00),
    ("Rogers",                   790.10),
]

REVENUE     = 102573.0
BUS_EXPENSE = 70081.0   # T2125 net (after CCA/home office)
TAX_CPP     = 6566.0
SAVINGS     = 36701.72
PER_EXPENSE = 78957.0

# Business expense actuals from the Business tab
BUS_ACTUALS = {
    "Advertising & Marketing": 3942,
    "Professional Fees":        146,
    "Vehicle":                 5234,
    "Insurance":                678,
    "Interest & Bank Charges":  660,
    "Office Supplies (<$500)": 11085,
    "Rent / Co-working":       9251,
    "Software & Subscriptions": 7989,
    "Travel":                  1323,
    "Telephone & Internet":    1250,
    "Subcontractors":           250,
    "Meals & Entertainment":   4542,
    "Home Office":             3480,
    "Equipment (CCA)":        12816,   # CCA allowable
    "Other Business":           570,
}

# Monthly budgets (set from 2025 actuals — conservative rounding)
BUDGETS = {
    "Advertising & Marketing":  400,
    "Professional Fees":         50,
    "Vehicle":                  450,
    "Insurance":                 60,
    "Interest & Bank Charges":   60,
    "Office Supplies (<$500)":  600,
    "Rent / Co-working":        800,
    "Software & Subscriptions": 700,
    "Travel":                   150,
    "Telephone & Internet":     110,
    "Subcontractors":            50,
    "Meals & Entertainment":    400,
    "Home Office":              290,
    "Equipment (CCA)":         1100,
    "Other Business":            60,
}

# Personal category actuals (from Personal tab)
PER_ACTUALS = {
    "Groceries":           4685,
    "Dining Out":          1988,
    "Transportation":       100,
    "Health & Fitness":     886,
    "Entertainment":        398,
    "Savings/Investments": 36702,
    "Other Personal":      34198,
}


def build_insights_data():
    """Returns list of (row, col, value) tuples for Insights tab values."""
    rows = []
    # We'll build the rows as value lists to write via update, and return
    # a structured list of sections with start row info
    return []  # actual writing done below


def main():
    service = get_sheets_service()
    ss = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    sheets = {s['properties']['title']: s['properties']['sheetId'] for s in ss['sheets']}

    print("Sheet IDs:", sheets)

    batch_requests = []

    # =========================================================================
    # STEP 1: Create Insights tab
    # =========================================================================
    if 'Insights' not in sheets:
        batch_requests.append({
            "addSheet": {
                "properties": {
                    "title": "Insights",
                    "index": 11,  # after Tax
                    "gridProperties": {"rowCount": 120, "columnCount": 10}
                }
            }
        })

    # Execute addSheet first so we get the ID
    if batch_requests:
        resp = service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": batch_requests}
        ).execute()
        # Refresh sheet list
        ss2 = service.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        sheets = {s['properties']['title']: s['properties']['sheetId'] for s in ss2['sheets']}
        batch_requests = []

    ins_id = sheets['Insights']
    bus_id = sheets['Business']
    per_id = sheets['Personal']
    dash_id = sheets['Dashboard']
    pl_id   = sheets['P&L']

    print(f"Insights sheet ID: {ins_id}")

    # =========================================================================
    # STEP 2: Write Insights data
    # =========================================================================
    # Build the full insights content
    # Layout: Col A=label, B=value/metric, C=label2, D=value2, E=notes
    # Cols: A(24), B(16), C(24), D(16), E(30) — indices 0-4

    ins_values = []

    def pad(lst, length, fill=''):
        return lst + [fill] * (length - len(lst))

    # Row 1: title
    ins_values.append(pad(['Insights  ·  Financial Intelligence  ·  2025'], 10))
    ins_values.append(pad(['Matt Anthony Photography'], 10))
    ins_values.append([])

    # ── Section 1: Cash Flow Analysis ─────────────────────────────────────────
    ins_values.append(pad(['CASH FLOW ANALYSIS'], 10))  # row 4 (0-indexed: 3)
    ins_values.append(pad(['Month', 'Income', 'Total Outflow', 'Net Surplus/Deficit', 'Cumul Balance', 'Flag'], 10))

    cumul = 0
    for i, m in enumerate(MONTHS, 1):
        inc = MONTHLY_INCOME[i]
        exp = MONTHLY_TOTAL_EXP[i]
        net = inc - exp
        cumul += net
        flag = 'DEFICIT ⚠' if net < 0 else ''
        ins_values.append(pad([m, inc, exp, net, cumul, flag], 10))

    ins_values.append([])

    # Summary stats
    nets = [MONTHLY_INCOME[i] - MONTHLY_TOTAL_EXP[i] for i in range(1,13)]
    avg_surplus = sum(nets) / 12
    deficit_months = sum(1 for n in nets if n < 0)
    ins_values.append(pad(['Average monthly surplus/deficit', avg_surplus, '', '', '', f'{deficit_months} of 12 months were deficits'], 10))
    ins_values.append([])

    section2_start = len(ins_values)  # track row

    # ── Section 2: Spending Velocity ──────────────────────────────────────────
    ins_values.append(pad(['SPENDING VELOCITY'], 10))
    total_spend = sum(MONTHLY_TOTAL_EXP.values())
    daily_avg = total_spend / 365
    weekly_burn = total_spend / 52
    annual_proj = daily_avg * 365
    ins_values.append(pad(['Daily average spend (all)', daily_avg, 'Annual projection', annual_proj], 10))
    ins_values.append(pad(['Weekly burn rate', weekly_burn, '', ''], 10))
    ins_values.append(pad(['Business-only daily avg', sum(MONTHLY_BUS_EXP.values())/365, '', ''], 10))
    ins_values.append([])

    section3_start = len(ins_values)

    # ── Section 3: Software Stack Cost ────────────────────────────────────────
    ins_values.append(pad(['SOFTWARE STACK COST'], 10))
    ins_values.append(pad(['Tool / Service', 'Annual Spend', 'Monthly Equiv', '% of Revenue'], 10))
    for name, annual in sorted(SOFTWARE_SUBS, key=lambda x: x[1], reverse=True):
        pct = annual / REVENUE
        ins_values.append(pad([name, annual, annual/12, pct], 10))
    ins_values.append([])
    sw_pct = SOFTWARE_TOTAL / REVENUE
    ins_values.append(pad(['TOTAL SOFTWARE', SOFTWARE_TOTAL, SOFTWARE_TOTAL/12, sw_pct, f'That\'s {sw_pct*100:.1f}% of your revenue'], 10))
    ins_values.append([])

    section4_start = len(ins_values)

    # ── Section 4: Savings Rate ────────────────────────────────────────────────
    ins_values.append(pad(['SAVINGS & INVESTMENTS'], 10))
    sav_pct = SAVINGS / REVENUE
    ins_values.append(pad(['Total saved (Questrade + Shakepay)', SAVINGS, '', ''], 10))
    ins_values.append(pad(['Savings as % of gross revenue', sav_pct, '', ''], 10))
    ins_values.append(pad(['Savings as % of net profit', SAVINGS / (REVENUE - BUS_EXPENSE), '', ''], 10))
    ins_values.append(pad(['RRSP note', '', '', '', '2025 RRSP room = 18% of 2024 earned income. Check MyAccount CRA.'], 10))
    ins_values.append([])

    section5_start = len(ins_values)

    # ── Section 5: Top 20 Vendors ─────────────────────────────────────────────
    ins_values.append(pad(['TOP 20 VENDORS BY TOTAL SPEND'], 10))
    ins_values.append(pad(['#', 'Vendor', 'Total Spend', '% of Revenue', 'Category'], 10))
    for rank, (vendor, total) in enumerate(TOP_VENDORS[:20], 1):
        pct = total / REVENUE
        ins_values.append(pad([rank, vendor, total, pct, ''], 10))
    ins_values.append([])

    section6_start = len(ins_values)

    # ── Section 6: Year-over-Year ──────────────────────────────────────────────
    ins_values.append(pad(['YEAR-OVER-YEAR COMPARISON'], 10))
    ins_values.append(pad(['Metric', '2024 Filed', '2025 Actual', 'Change', '% Growth'], 10))
    yoy_data = [
        ('Gross Revenue',         75000,   REVENUE,     REVENUE - 75000,      (REVENUE - 75000)/75000),
        ('Net Business Income',   20800,   REVENUE - BUS_EXPENSE, (REVENUE - BUS_EXPENSE) - 20800, ((REVENUE - BUS_EXPENSE) - 20800)/20800),
        ('Total Tax + CPP',         534,   TAX_CPP,     TAX_CPP - 534,        (TAX_CPP - 534)/534),
        ('Savings/Investments',       0,   SAVINGS,     SAVINGS - 0,          None),
    ]
    for label, y24, y25, chg, pct_chg in yoy_data:
        pct_str = f'{pct_chg*100:.1f}%' if pct_chg is not None else 'N/A'
        ins_values.append(pad([label, y24, y25, chg, pct_str], 10))
    ins_values.append([])

    # Write all to Insights tab
    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range='Insights!A1',
        valueInputOption='USER_ENTERED',
        body={'values': ins_values}
    ).execute()
    print(f"Wrote {len(ins_values)} rows to Insights tab")

    # =========================================================================
    # STEP 3: Format Insights tab
    # =========================================================================
    fmt_reqs = []

    def section_header_fmt(row_0, col_end=9):
        return [
            {
                "repeatCell": {
                    "range": grid_range(ins_id, row_0, row_0+1, 0, col_end),
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": DARK_BG,
                            "textFormat": {"bold": True, "fontSize": 11, "fontFamily": "Inter",
                                           "foregroundColor": WHITE},
                            "padding": {"left": 8}
                        }
                    },
                    "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.padding"
                }
            },
            set_row_height(ins_id, row_0, 28),
        ]

    def col_header_fmt(row_0, col_start=0, col_end=9):
        return [{
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, col_start, col_end),
                "cell": {
                    "userEnteredFormat": {
                        "backgroundColor": WHITE,
                        "textFormat": {"bold": True, "fontSize": 9, "fontFamily": "Inter",
                                       "foregroundColor": GRAY_HDR},
                        "borders": {"bottom": {"style": "SOLID", "width": 1, "color": MID_GRAY}}
                    }
                },
                "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.borders"
            }
        }]

    # Title rows 1-2 (0-indexed: 0-1)
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(ins_id, 0, 1, 0, 8),
            "cell": {"userEnteredFormat": {
                "textFormat": {"bold": True, "fontSize": 14, "fontFamily": "Inter",
                               "foregroundColor": NAVY},
            }},
            "fields": "userEnteredFormat.textFormat"
        }
    })
    fmt_reqs.append(merge(ins_id, 0, 1, 0, 8))
    fmt_reqs.append(set_row_height(ins_id, 0, 32))

    # Section 1: Cash Flow — header at row 3 (0-indexed), col headers at row 4
    fmt_reqs.extend(section_header_fmt(3))
    fmt_reqs.extend(col_header_fmt(4))

    # Data rows 5-16 (12 months), alternate shading
    cash_start = 5
    for i in range(12):
        row_0 = cash_start + i
        bg_color = WHITE if i % 2 == 0 else ALT_ROW
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 0, 6),
                "cell": {"userEnteredFormat": {"backgroundColor": bg_color}},
                "fields": "userEnteredFormat.backgroundColor"
            }
        })
        # Format Income col (B=1) blue
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 1, 2),
                "cell": {"userEnteredFormat": {
                    "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"},
                    "textFormat": {"foregroundColor": BLUE_REV}
                }},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.textFormat"
            }
        })
        # Total outflow (C=2) red
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 2, 3),
                "cell": {"userEnteredFormat": {
                    "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"},
                    "textFormat": {"foregroundColor": RED_EXP}
                }},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.textFormat"
            }
        })
        # Net (D=3) green/red conditional via formatting (just money format, color set below)
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 3, 5),
                "cell": {"userEnteredFormat": {
                    "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0;($#,##0)"},
                }},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # Summary row after months
    summary_row = cash_start + 13  # +12 months + 1 blank
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(ins_id, summary_row, summary_row+1, 0, 6),
            "cell": {"userEnteredFormat": {
                "backgroundColor": LIGHT_BLUE,
                "textFormat": {"bold": True, "fontFamily": "Inter"},
                "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.numberFormat"
        }
    })

    # Section 2: Spending Velocity — section2_start
    sv_row = section2_start
    fmt_reqs.extend(section_header_fmt(sv_row))
    for i in range(1, 5):
        row_0 = sv_row + i
        bg_color = WHITE if i % 2 == 1 else ALT_ROW
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 0, 5),
                "cell": {"userEnteredFormat": {
                    "backgroundColor": bg_color,
                    "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}
                }},
                "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.numberFormat"
            }
        })
        # Label cols not currency
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 0, 1),
                "cell": {"userEnteredFormat": {
                    "numberFormat": {"type": "TEXT"}
                }},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # Section 3: Software Stack — section3_start
    sw_header_row = section3_start
    fmt_reqs.extend(section_header_fmt(sw_header_row))
    fmt_reqs.extend(col_header_fmt(sw_header_row + 1))
    sw_data_start = sw_header_row + 2
    sw_data_end = sw_data_start + len(SOFTWARE_SUBS)
    for i in range(len(SOFTWARE_SUBS)):
        row_0 = sw_data_start + i
        bg_color = WHITE if i % 2 == 0 else ALT_ROW
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 0, 5),
                "cell": {"userEnteredFormat": {"backgroundColor": bg_color}},
                "fields": "userEnteredFormat.backgroundColor"
            }
        })
        # Annual spend col (B=1)
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 1, 3),
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })
        # % col (D=3)
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 3, 4),
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.00%"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # Software total row
    sw_total_row = sw_data_end + 1
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(ins_id, sw_total_row, sw_total_row+1, 0, 5),
            "cell": {"userEnteredFormat": {
                "backgroundColor": LIGHT_ORG,
                "textFormat": {"bold": True, "fontFamily": "Inter"},
                "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.numberFormat"
        }
    })
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(ins_id, sw_total_row, sw_total_row+1, 3, 4),
            "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}},
            "fields": "userEnteredFormat.numberFormat"
        }
    })

    # Section 4: Savings — section4_start
    sav_row = section4_start
    fmt_reqs.extend(section_header_fmt(sav_row))
    for i in range(1, 5):
        row_0 = sav_row + i
        bg_color = LIGHT_GRN if i % 2 == 1 else WHITE
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 0, 5),
                "cell": {"userEnteredFormat": {"backgroundColor": bg_color}},
                "fields": "userEnteredFormat.backgroundColor"
            }
        })
        if i in (1, 2, 3):
            fmt_reqs.append({
                "repeatCell": {
                    "range": grid_range(ins_id, row_0, row_0+1, 1, 2),
                    "cell": {"userEnteredFormat": {
                        "numberFormat": {"type": "CURRENCY" if i == 1 else "PERCENT",
                                         "pattern": "$#,##0" if i == 1 else "0.0%"},
                        "textFormat": {"foregroundColor": GREEN_PRF, "bold": True, "fontFamily": "Inter"}
                    }},
                    "fields": "userEnteredFormat.numberFormat,userEnteredFormat.textFormat"
                }
            })

    # Section 5: Top 20 Vendors — section5_start
    top_row = section5_start
    fmt_reqs.extend(section_header_fmt(top_row))
    fmt_reqs.extend(col_header_fmt(top_row + 1))
    top_data_start = top_row + 2
    for i in range(20):
        row_0 = top_data_start + i
        bg_color = WHITE if i % 2 == 0 else ALT_ROW
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 0, 5),
                "cell": {"userEnteredFormat": {"backgroundColor": bg_color}},
                "fields": "userEnteredFormat.backgroundColor"
            }
        })
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 2, 3),
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 3, 4),
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "PERCENT", "pattern": "0.0%"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # Section 6: YoY — section6_start
    yoy_row = section6_start
    fmt_reqs.extend(section_header_fmt(yoy_row))
    fmt_reqs.extend(col_header_fmt(yoy_row + 1))
    yoy_data_start = yoy_row + 2
    yoy_rows_data = [
        ('Gross Revenue', 75000, REVENUE, REVENUE - 75000, (REVENUE - 75000)/75000),
        ('Net Business Income', 20800, REVENUE - BUS_EXPENSE, (REVENUE - BUS_EXPENSE) - 20800, ((REVENUE - BUS_EXPENSE) - 20800)/20800),
        ('Total Tax + CPP', 534, TAX_CPP, TAX_CPP - 534, (TAX_CPP - 534)/534),
        ('Savings/Investments', 0, SAVINGS, SAVINGS, None),
    ]
    for i in range(len(yoy_rows_data)):
        row_0 = yoy_data_start + i
        bg_color = LIGHT_BLUE if i % 2 == 0 else WHITE
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 0, 5),
                "cell": {"userEnteredFormat": {
                    "backgroundColor": bg_color,
                    "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}
                }},
                "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.numberFormat"
            }
        })
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(ins_id, row_0, row_0+1, 0, 1),
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # Column widths for Insights
    col_widths = [200, 120, 200, 100, 110, 200, 100, 100, 100, 100]
    for ci, w in enumerate(col_widths):
        fmt_reqs.append(set_col_width(ins_id, ci, w))

    # Freeze row 1
    fmt_reqs.append({
        "updateSheetProperties": {
            "properties": {"sheetId": ins_id, "gridProperties": {"frozenRowCount": 1}},
            "fields": "gridProperties.frozenRowCount"
        }
    })

    # =========================================================================
    # STEP 4: Update Business tab — Monthly Budget vs Actual section
    # =========================================================================
    # Find where to append — after row 18 (TOTAL), leave a gap, start at row 21
    bus_insert_row = 21  # 1-indexed (rows 19=blank, 20=blank, 21=header)

    bus_budget_values = [
        [],
        [],
        ['MONTHLY BUDGET vs ACTUAL  ·  2025'],
        ['Category', 'Annual Budget', 'Monthly Budget', '2025 Actual', 'Monthly Avg', 'Variance (Annual)', 'Status'],
    ]
    for cat, actual in BUS_ACTUALS.items():
        budget_mo = BUDGETS.get(cat, 0)
        budget_ann = budget_mo * 12
        monthly_avg = actual / 12
        variance = actual - budget_ann
        status = 'OVER' if variance > 0 else 'ON TRACK'
        bus_budget_values.append([cat, budget_ann, budget_mo, actual, monthly_avg, variance, status])

    # Total row
    total_budget_ann = sum(BUDGETS[c]*12 for c in BUDGETS)
    total_actual = sum(BUS_ACTUALS.values())
    total_variance = total_actual - total_budget_ann
    bus_budget_values.append([
        'TOTAL', total_budget_ann, total_budget_ann/12,
        total_actual, total_actual/12, total_variance,
        'OVER' if total_variance > 0 else 'ON TRACK'
    ])

    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f'Business!A{bus_insert_row}',
        valueInputOption='USER_ENTERED',
        body={'values': bus_budget_values}
    ).execute()
    print(f"Wrote Budget vs Actual to Business tab at row {bus_insert_row}")

    # Format Business Budget section
    bus_sec_row0 = bus_insert_row + 2 - 1  # 0-indexed: row 22 → index 22
    bus_hdr_row0 = bus_sec_row0 + 1
    bus_data_start0 = bus_hdr_row0 + 1

    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(bus_id, bus_sec_row0, bus_sec_row0+1, 0, 7),
            "cell": {"userEnteredFormat": {
                "backgroundColor": DARK_BG,
                "textFormat": {"bold": True, "fontSize": 11, "fontFamily": "Inter",
                               "foregroundColor": WHITE},
                "padding": {"left": 8}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.padding"
        }
    })
    fmt_reqs.append(merge(bus_id, bus_sec_row0, bus_sec_row0+1, 0, 7))
    fmt_reqs.append(set_row_height(bus_id, bus_sec_row0, 28))

    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(bus_id, bus_hdr_row0, bus_hdr_row0+1, 0, 7),
            "cell": {"userEnteredFormat": {
                "backgroundColor": WHITE,
                "textFormat": {"bold": True, "fontSize": 9, "fontFamily": "Inter",
                               "foregroundColor": GRAY_HDR},
                "borders": {"bottom": {"style": "SOLID", "width": 1, "color": MID_GRAY}}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.borders"
        }
    })

    num_bus_cats = len(BUS_ACTUALS)
    for i in range(num_bus_cats):
        row_0 = bus_data_start0 + i
        bg_color = WHITE if i % 2 == 0 else ALT_ROW
        # Check for OVER variance
        cat = list(BUS_ACTUALS.keys())[i]
        actual = BUS_ACTUALS[cat]
        budget = BUDGETS.get(cat, 0) * 12
        is_over = actual > budget
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(bus_id, row_0, row_0+1, 0, 7),
                "cell": {"userEnteredFormat": {"backgroundColor": LIGHT_RED if is_over else bg_color}},
                "fields": "userEnteredFormat.backgroundColor"
            }
        })
        # Currency cols B-F (1-5)
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(bus_id, row_0, row_0+1, 1, 6),
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })
        # Status col G (6) bold red/green
        status_color = RED_EXP if is_over else GREEN_PRF
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(bus_id, row_0, row_0+1, 6, 7),
                "cell": {"userEnteredFormat": {
                    "textFormat": {"bold": True, "foregroundColor": status_color, "fontFamily": "Inter"},
                }},
                "fields": "userEnteredFormat.textFormat"
            }
        })

    # Total row
    bus_total_row0 = bus_data_start0 + num_bus_cats
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(bus_id, bus_total_row0, bus_total_row0+1, 0, 7),
            "cell": {"userEnteredFormat": {
                "backgroundColor": LIGHT_ORG,
                "textFormat": {"bold": True, "fontFamily": "Inter"},
                "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.numberFormat"
        }
    })

    # =========================================================================
    # STEP 5: Update Personal tab — Spending Insights section
    # =========================================================================
    per_insert_row = 18  # after row 15 total + blank

    per_insight_values = [
        [],
        [],
        ['PERSONAL SPENDING INSIGHTS  ·  2025'],
        ['Metric', 'Value', 'Notes'],
    ]

    total_per = sum(PER_ACTUALS.values())
    daily_per = total_per / 365
    dining_pct = PER_ACTUALS.get('Dining Out', 0) / total_per
    grocery_dining_ratio = PER_ACTUALS.get('Groceries', 0) / max(PER_ACTUALS.get('Dining Out', 1), 1)

    # Find largest non-savings category
    non_sav = {k: v for k, v in PER_ACTUALS.items() if k != 'Savings/Investments'}
    largest_cat = max(non_sav, key=non_sav.get)

    per_insight_values += [
        ['Daily average spend (personal)', daily_per, ''],
        ['Total personal spending', total_per, 'incl. savings'],
        ['Total personal (excl. savings)', total_per - SAVINGS, ''],
        ['Dining Out as % of total personal', dining_pct, ''],
        ['Groceries vs Dining ratio', grocery_dining_ratio, f'${PER_ACTUALS["Groceries"]:,.0f} groceries : ${PER_ACTUALS["Dining Out"]:,.0f} dining'],
        ['Largest personal category', largest_cat, f'${non_sav[largest_cat]:,.0f}'],
        ['Savings/Investments', SAVINGS, f'{SAVINGS/REVENUE*100:.1f}% of gross revenue'],
    ]

    # Monthly personal trend
    per_insight_values.append([])
    per_insight_values.append(['Monthly Personal Trend', '', ''])
    per_insight_values.append(['Month', 'Total Personal', 'Excl. Savings'])
    for i, m in enumerate(MONTHS, 1):
        per_exp = MONTHLY_PER_EXP[i]
        # Savings monthly (approximate from Savings/Investments row in Personal tab)
        per_insight_values.append([m, per_exp, ''])

    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f'Personal!A{per_insert_row}',
        valueInputOption='USER_ENTERED',
        body={'values': per_insight_values}
    ).execute()
    print(f"Wrote Personal Spending Insights to Personal tab at row {per_insert_row}")

    # Format Personal Insights section
    per_sec_row0 = per_insert_row + 2 - 1  # 0-indexed
    per_hdr_row0 = per_sec_row0 + 1
    per_data_start0 = per_hdr_row0 + 1

    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(per_id, per_sec_row0, per_sec_row0+1, 0, 5),
            "cell": {"userEnteredFormat": {
                "backgroundColor": DARK_BG,
                "textFormat": {"bold": True, "fontSize": 11, "fontFamily": "Inter",
                               "foregroundColor": WHITE},
                "padding": {"left": 8}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.padding"
        }
    })
    fmt_reqs.append(merge(per_id, per_sec_row0, per_sec_row0+1, 0, 5))
    fmt_reqs.append(set_row_height(per_id, per_sec_row0, 28))

    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(per_id, per_hdr_row0, per_hdr_row0+1, 0, 4),
            "cell": {"userEnteredFormat": {
                "backgroundColor": WHITE,
                "textFormat": {"bold": True, "fontSize": 9, "fontFamily": "Inter",
                               "foregroundColor": GRAY_HDR},
                "borders": {"bottom": {"style": "SOLID", "width": 1, "color": MID_GRAY}}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.borders"
        }
    })

    per_metric_rows = 7
    for i in range(per_metric_rows):
        row_0 = per_data_start0 + i
        bg_color = WHITE if i % 2 == 0 else ALT_ROW
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(per_id, row_0, row_0+1, 0, 4),
                "cell": {"userEnteredFormat": {"backgroundColor": bg_color}},
                "fields": "userEnteredFormat.backgroundColor"
            }
        })
        # Value col (B=1) — currency for dollar rows, percent for pct rows, number for ratio
        if i == 0:  # daily avg
            num_fmt = {"type": "CURRENCY", "pattern": "$#,##0.00"}
        elif i in (1, 2, 6):  # totals
            num_fmt = {"type": "CURRENCY", "pattern": "$#,##0"}
        elif i == 3:  # dining pct
            num_fmt = {"type": "PERCENT", "pattern": "0.0%"}
        elif i == 4:  # ratio
            num_fmt = {"type": "NUMBER", "pattern": "0.0"}
        else:
            num_fmt = {"type": "TEXT"}
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(per_id, row_0, row_0+1, 1, 2),
                "cell": {"userEnteredFormat": {"numberFormat": num_fmt}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # Monthly trend sub-section (starts at per_data_start0 + 8 + 1 = +9)
    per_trend_hdr = per_data_start0 + 8 + 1
    per_trend_data = per_trend_hdr + 1
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(per_id, per_trend_hdr - 1, per_trend_hdr, 0, 3),
            "cell": {"userEnteredFormat": {
                "textFormat": {"bold": True, "fontSize": 9, "fontFamily": "Inter",
                               "foregroundColor": NAVY}
            }},
            "fields": "userEnteredFormat.textFormat"
        }
    })
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(per_id, per_trend_hdr, per_trend_hdr+1, 0, 3),
            "cell": {"userEnteredFormat": {
                "backgroundColor": WHITE,
                "textFormat": {"bold": True, "fontSize": 9, "fontFamily": "Inter",
                               "foregroundColor": GRAY_HDR},
                "borders": {"bottom": {"style": "SOLID", "width": 1, "color": MID_GRAY}}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.borders"
        }
    })
    for i in range(12):
        row_0 = per_trend_data + i
        bg_color = WHITE if i % 2 == 0 else ALT_ROW
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(per_id, row_0, row_0+1, 0, 3),
                "cell": {"userEnteredFormat": {
                    "backgroundColor": bg_color,
                    "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}
                }},
                "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.numberFormat"
            }
        })
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(per_id, row_0, row_0+1, 0, 1),
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "TEXT"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })

    # =========================================================================
    # STEP 6: Update Dashboard — Cash Flow Bar + Key Ratios
    # =========================================================================
    # Dashboard currently ends around row 32. Add from row 36.
    dash_insert_row = 36

    dash_values = [
        [],
        [],
        ['', '', 'Monthly Cash Flow  ·  Net Surplus / Deficit'],
        ['', '', 'Month', 'Revenue', 'Total Outflow', 'Net', 'Cumul Balance'],
    ]

    cumul = 0
    for i, m in enumerate(MONTHS, 1):
        inc = MONTHLY_INCOME[i]
        exp = MONTHLY_TOTAL_EXP[i]
        net = inc - exp
        cumul += net
        dash_values.append(['', '', m, inc, exp, net, cumul])

    dash_values.append(['', '', 'Total', sum(MONTHLY_INCOME.values()), sum(MONTHLY_TOTAL_EXP.values()),
                        sum(MONTHLY_INCOME.values()) - sum(MONTHLY_TOTAL_EXP.values()), ''])
    dash_values.append([])
    dash_values.append([])

    # Key Ratios section
    profit_margin = (REVENUE - BUS_EXPENSE) / REVENUE
    expense_ratio = BUS_EXPENSE / REVENUE
    savings_rate_pct = SAVINGS / REVENUE
    sw_pct_rev = SOFTWARE_TOTAL / REVENUE
    vehicle_pct = 5234 / REVENUE

    dash_values += [
        ['', '', 'Key Ratios  ·  2025'],
        ['', '', 'Metric', 'Value', '2024 Reference', 'Notes'],
        ['', '', 'Profit Margin (business)',      profit_margin,    '',        f'Net ${REVENUE - BUS_EXPENSE:,.0f} on ${REVENUE:,.0f} revenue'],
        ['', '', 'Business Expense Ratio',         expense_ratio,    '0.640',   '2024 was 64% of revenue'],
        ['', '', 'Savings Rate',                   savings_rate_pct, '',        f'${SAVINGS:,.0f} invested'],
        ['', '', 'Software as % of Revenue',       sw_pct_rev,       '',        f'${SOFTWARE_TOTAL:,.0f}/yr total stack'],
        ['', '', 'Vehicle as % of Revenue',        vehicle_pct,      '',        f'${5234:,.0f} total vehicle'],
        ['', '', 'Revenue Growth (vs 2024)',        (REVENUE - 75000)/75000, '', f'+${REVENUE - 75000:,.0f} over 2024'],
    ]

    service.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f'Dashboard!A{dash_insert_row}',
        valueInputOption='USER_ENTERED',
        body={'values': dash_values}
    ).execute()
    print(f"Wrote Cash Flow + Key Ratios to Dashboard at row {dash_insert_row}")

    # Format Dashboard additions
    dash_cf_hdr_row0  = dash_insert_row + 2 - 1   # "Monthly Cash Flow" header
    dash_col_hdr_row0 = dash_cf_hdr_row0 + 1
    dash_cf_data0     = dash_col_hdr_row0 + 1

    # Section header
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(dash_id, dash_cf_hdr_row0, dash_cf_hdr_row0+1, 2, 9),
            "cell": {"userEnteredFormat": {
                "backgroundColor": DARK_BG,
                "textFormat": {"bold": True, "fontSize": 11, "fontFamily": "Inter",
                               "foregroundColor": WHITE},
                "padding": {"left": 8}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.padding"
        }
    })
    fmt_reqs.append(set_row_height(dash_id, dash_cf_hdr_row0, 28))

    # Col headers
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(dash_id, dash_col_hdr_row0, dash_col_hdr_row0+1, 2, 9),
            "cell": {"userEnteredFormat": {
                "backgroundColor": WHITE,
                "textFormat": {"bold": True, "fontSize": 9, "fontFamily": "Inter",
                               "foregroundColor": GRAY_HDR},
                "borders": {"bottom": {"style": "SOLID", "width": 1, "color": MID_GRAY}}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.borders"
        }
    })

    # 12 months data
    for i in range(12):
        row_0 = dash_cf_data0 + i
        bg_color = WHITE if i % 2 == 0 else ALT_ROW
        nets_val = MONTHLY_INCOME[i+1] - MONTHLY_TOTAL_EXP[i+1]
        bg_override = LIGHT_RED if nets_val < 0 else bg_color
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(dash_id, row_0, row_0+1, 2, 9),
                "cell": {"userEnteredFormat": {"backgroundColor": bg_override}},
                "fields": "userEnteredFormat.backgroundColor"
            }
        })
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(dash_id, row_0, row_0+1, 3, 7),
                "cell": {"userEnteredFormat": {"numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}}},
                "fields": "userEnteredFormat.numberFormat"
            }
        })
        # Net col (F=5 → col index 5) color
        net_color = RED_EXP if nets_val < 0 else GREEN_PRF
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(dash_id, row_0, row_0+1, 5, 6),
                "cell": {"userEnteredFormat": {
                    "textFormat": {"bold": True, "foregroundColor": net_color, "fontFamily": "Inter"}
                }},
                "fields": "userEnteredFormat.textFormat"
            }
        })

    # Total row
    dash_total_row0 = dash_cf_data0 + 12
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(dash_id, dash_total_row0, dash_total_row0+1, 2, 9),
            "cell": {"userEnteredFormat": {
                "backgroundColor": LIGHT_BLUE,
                "textFormat": {"bold": True, "fontFamily": "Inter"},
                "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0"}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.numberFormat"
        }
    })

    # Key Ratios section header
    kr_sec_row0 = dash_total_row0 + 3
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(dash_id, kr_sec_row0, kr_sec_row0+1, 2, 9),
            "cell": {"userEnteredFormat": {
                "backgroundColor": DARK_BG,
                "textFormat": {"bold": True, "fontSize": 11, "fontFamily": "Inter",
                               "foregroundColor": WHITE},
                "padding": {"left": 8}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.padding"
        }
    })
    fmt_reqs.append(merge(dash_id, kr_sec_row0, kr_sec_row0+1, 2, 9))
    fmt_reqs.append(set_row_height(dash_id, kr_sec_row0, 28))

    kr_col_hdr0 = kr_sec_row0 + 1
    fmt_reqs.append({
        "repeatCell": {
            "range": grid_range(dash_id, kr_col_hdr0, kr_col_hdr0+1, 2, 7),
            "cell": {"userEnteredFormat": {
                "backgroundColor": WHITE,
                "textFormat": {"bold": True, "fontSize": 9, "fontFamily": "Inter",
                               "foregroundColor": GRAY_HDR},
                "borders": {"bottom": {"style": "SOLID", "width": 1, "color": MID_GRAY}}
            }},
            "fields": "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.borders"
        }
    })

    kr_data0 = kr_col_hdr0 + 1
    ratio_rows = 6
    ratio_colors = [GREEN_PRF, RED_EXP, GREEN_PRF, ORANGE, ORANGE, BLUE_REV]
    for i in range(ratio_rows):
        row_0 = kr_data0 + i
        bg_color = WHITE if i % 2 == 0 else ALT_ROW
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(dash_id, row_0, row_0+1, 2, 7),
                "cell": {"userEnteredFormat": {"backgroundColor": bg_color}},
                "fields": "userEnteredFormat.backgroundColor"
            }
        })
        fmt_reqs.append({
            "repeatCell": {
                "range": grid_range(dash_id, row_0, row_0+1, 3, 4),
                "cell": {"userEnteredFormat": {
                    "numberFormat": {"type": "PERCENT", "pattern": "0.0%"},
                    "textFormat": {"bold": True, "foregroundColor": ratio_colors[i], "fontFamily": "Inter"}
                }},
                "fields": "userEnteredFormat.numberFormat,userEnteredFormat.textFormat"
            }
        })

    # =========================================================================
    # STEP 7: Add Charts to P&L tab
    # =========================================================================
    # Revenue vs Expenses bar chart
    chart1 = {
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Monthly Revenue vs Business Expenses — 2025",
                    "basicChart": {
                        "chartType": "BAR",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "title": "Amount (CAD)"},
                            {"position": "LEFT_AXIS", "title": "Month"},
                        ],
                        "domains": [{
                            "domain": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": pl_id,
                                        "startRowIndex": 1, "endRowIndex": 13,
                                        "startColumnIndex": 0, "endColumnIndex": 1
                                    }]
                                }
                            }
                        }],
                        "series": [
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": pl_id,
                                            "startRowIndex": 1, "endRowIndex": 13,
                                            "startColumnIndex": 1, "endColumnIndex": 2
                                        }]
                                    }
                                },
                                "targetAxis": "BOTTOM_AXIS",
                                "color": {"red": 0.051, "green": 0.278, "blue": 0.631}
                            },
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": pl_id,
                                            "startRowIndex": 1, "endRowIndex": 13,
                                            "startColumnIndex": 2, "endColumnIndex": 3
                                        }]
                                    }
                                },
                                "targetAxis": "BOTTOM_AXIS",
                                "color": {"red": 0.827, "green": 0.184, "blue": 0.184}
                            }
                        ],
                        "headerCount": 0
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": pl_id,
                            "rowIndex": 16,
                            "columnIndex": 0
                        },
                        "offsetXPixels": 0,
                        "offsetYPixels": 0,
                        "widthPixels": 500,
                        "heightPixels": 320
                    }
                }
            }
        }
    }

    # Cumulative Profit line chart
    chart2 = {
        "addChart": {
            "chart": {
                "spec": {
                    "title": "Cumulative Profit — 2025",
                    "basicChart": {
                        "chartType": "LINE",
                        "legendPosition": "BOTTOM_LEGEND",
                        "axis": [
                            {"position": "BOTTOM_AXIS", "title": "Month"},
                            {"position": "LEFT_AXIS", "title": "Cumulative Profit (CAD)"},
                        ],
                        "domains": [{
                            "domain": {
                                "sourceRange": {
                                    "sources": [{
                                        "sheetId": pl_id,
                                        "startRowIndex": 1, "endRowIndex": 13,
                                        "startColumnIndex": 0, "endColumnIndex": 1
                                    }]
                                }
                            }
                        }],
                        "series": [
                            {
                                "series": {
                                    "sourceRange": {
                                        "sources": [{
                                            "sheetId": pl_id,
                                            "startRowIndex": 1, "endRowIndex": 13,
                                            "startColumnIndex": 6, "endColumnIndex": 7
                                        }]
                                    }
                                },
                                "targetAxis": "LEFT_AXIS",
                                "color": {"red": 0.149, "green": 0.588, "blue": 0.388}
                            }
                        ],
                        "headerCount": 0
                    }
                },
                "position": {
                    "overlayPosition": {
                        "anchorCell": {
                            "sheetId": pl_id,
                            "rowIndex": 16,
                            "columnIndex": 6
                        },
                        "offsetXPixels": 0,
                        "offsetYPixels": 0,
                        "widthPixels": 500,
                        "heightPixels": 320
                    }
                }
            }
        }
    }

    fmt_reqs.append(chart1)
    fmt_reqs.append(chart2)

    # =========================================================================
    # EXECUTE ALL FORMAT REQUESTS
    # =========================================================================
    # Split into batches of 50 to avoid API limits
    BATCH_SIZE = 50
    total = len(fmt_reqs)
    print(f"\nApplying {total} formatting requests...")
    for start in range(0, total, BATCH_SIZE):
        batch = fmt_reqs[start:start+BATCH_SIZE]
        service.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"requests": batch}
        ).execute()
        print(f"  Applied requests {start+1}–{min(start+BATCH_SIZE, total)}")

    print("\nAll done! Summary:")
    print("  ✓ Created 'Insights' tab with:")
    print("     - Cash Flow Analysis (12-month income vs outflow + running balance)")
    print("     - Spending Velocity (daily/weekly burn rates)")
    print(f"    - Software Stack Cost ({len(SOFTWARE_SUBS)} tools, ${SOFTWARE_TOTAL:,.0f}/yr)")
    print(f"    - Savings & Investments (${SAVINGS:,.0f}, {SAVINGS/REVENUE*100:.1f}% of revenue)")
    print("     - Top 20 Vendors by Spend")
    print("     - Year-over-Year Comparison (2024 vs 2025)")
    print("  ✓ Added 'Monthly Budget vs Actual' to Business tab (row 21+)")
    print("  ✓ Added 'Personal Spending Insights' to Personal tab (row 18+)")
    print("  ✓ Added 'Monthly Cash Flow Bar' + 'Key Ratios' to Dashboard (row 36+)")
    print("  ✓ Added 2 charts to P&L tab (Revenue vs Expenses bar, Cumulative Profit line)")


if __name__ == '__main__':
    main()
