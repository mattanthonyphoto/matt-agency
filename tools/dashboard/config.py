"""Dashboard configuration — sheet IDs, API endpoints, business constants."""

import os

# ---------------------------------------------------------------------------
# Google Sheets IDs
# ---------------------------------------------------------------------------
FINANCE_2026_SHEET_ID = os.getenv(
    "FINANCE_SHEET_2026_ID", "1fPpOPnAYEnfCu33h1ki9NzFGTUOkpgd4mMSQX_sT9CY"
)
FINANCE_2025_SHEET_ID = os.getenv(
    "FINANCE_SHEET_2025_ID", "1TyX4sOIo6CxblxjNM9Yft5h5vZO_BGhQjHlgC0uzQtI"
)
COLD_EMAIL_INPUT_ID = "1qaeT6nURloVQx48dPtJODUz55IrqQEyRJ5xmnJJjoVs"
COLD_EMAIL_OUTPUT_ID = "1brgQYbtCZwH1fFS3vYjMaW9IGf8iK37qeDBY2l06r8A"
PIPELINE_SHEET_ID = "1m8q6yIqq3jzYGkLwgFVD6d_WlAzMFgz-gRekdysE1IQ"

# ---------------------------------------------------------------------------
# GoHighLevel
# ---------------------------------------------------------------------------
GHL_BASE_URL = "https://services.leadconnectorhq.com"
GHL_API_VERSION = "2021-07-28"
GHL_PAGE_SIZE = 100

# ---------------------------------------------------------------------------
# Business constants (2026)
# ---------------------------------------------------------------------------
REVENUE_TARGET_2026 = 172_900
RECURRING_MONTHLY = 1_417.50
AOS_MARGIN_FLOOR = 0.40
CAPACITY_PAUSE_THRESHOLD = 3

# ---------------------------------------------------------------------------
# Sheet tab ranges — used by batchGet
# ---------------------------------------------------------------------------
FINANCE_RANGES_2026 = {
    "transactions": "Transactions!A1:N",
    "income": "Income!A1:R50",
    "expenses": "Business!A1:R50",
    "p_and_l": "P&L!A1:N50",
    "mileage": "Mileage!A1:G",
    "gst": "GST!A1:N30",
    "equipment": "Equipment!A1:L35",
    "tax": "Tax!A1:L30",
}

FINANCE_RANGES_2025 = {
    "transactions": "Transactions!A1:N",
    "income": "Income!A1:R50",
}

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
