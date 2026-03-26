"""
Import personal Visa •1351 transactions into the 2025 finance Google Sheet.
Sheet ID: 1TyX4sOIo6CxblxjNM9Yft5h5vZO_BGhQjHlgC0uzQtI
Headers at row 4, data starts at row 5.
"""
import csv
import os
import sys
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service

SHEET_ID = "1TyX4sOIo6CxblxjNM9Yft5h5vZO_BGhQjHlgC0uzQtI"
CSV_PATH = "/Users/matthewfernandes/Downloads/download-transactions (4).csv"

# ── Categorization rules ──────────────────────────────────────────────────────
# (regex_pattern, is_business, category, clean_name, split_pct)
# Rules are evaluated top-to-bottom; first match wins.
RULES = [
    # ── 100% Business — Software & Subscriptions ──────────────────────────────
    (r"FACEBK|FACEBOOK", True, "Advertising & Marketing", "Facebook Ads", 100),
    (r"HIGHLEVEL|GOHIGHLEVEL", True, "Software & Subscriptions", "GoHighLevel (CRM)", 100),
    (r"INSTANTLY", True, "Software & Subscriptions", "Instantly (Cold Email)", 100),
    (r"LEADGENJAY", True, "Software & Subscriptions", "LeadGenJay", 100),
    (r"ADOBE.*ADOBE|Adobe Inc", True, "Software & Subscriptions", "Adobe Creative Cloud", 100),
    (r"OPENAI|CHATGPT", True, "Software & Subscriptions", "OpenAI / ChatGPT", 100),
    (r"XAI LLC|X\.AI", True, "Software & Subscriptions", "xAI (Grok)", 100),
    (r"GOOGLE.*WORKSPACE|GOOGLE.*GSUITE", True, "Software & Subscriptions", "Google Workspace", 100),
    (r"Dropbox", True, "Software & Subscriptions", "Dropbox", 100),
    (r"Audible", True, "Software & Subscriptions", "Audible (Prof Dev)", 100),
    (r"SQSP\*", True, "Software & Subscriptions", "Squarespace", 100),
    (r"WWW\.AUTOIGDM|AUTOIGDM", True, "Software & Subscriptions", "AutoIGDM (Instagram)", 100),
    (r"SHEETMAGIC", True, "Software & Subscriptions", "SheetMagic", 100),
    (r"MATTANTHONYPHOTO", True, "Software & Subscriptions", "MattAnthonyPhoto (Domain)", 100),
    (r"CANVA", True, "Software & Subscriptions", "Canva", 100),
    (r"BUFFER", True, "Software & Subscriptions", "Buffer (Social Media)", 100),
    (r"QWILR", True, "Software & Subscriptions", "Qwilr (Proposals)", 100),
    (r"TINYPNG", True, "Software & Subscriptions", "TinyPNG Pro", 100),
    (r"SOUNDSTRIPE", True, "Software & Subscriptions", "Soundstripe (Music)", 100),
    (r"TRUSTED LEADS|TRUSTEDLEADS", True, "Software & Subscriptions", "Trusted Leads", 100),
    (r"PROEDU|SP PRO EDU", True, "Software & Subscriptions", "ProEdu (Education)", 100),
    (r"SP OPEN DOOR|OPEN DOOR PLATFORMS", True, "Software & Subscriptions", "Open Door Platforms", 100),
    (r"CLICKUP", True, "Software & Subscriptions", "ClickUp", 100),
    (r"EpidemicSound", True, "Software & Subscriptions", "Epidemic Sound (Music)", 100),
    (r"INTUIT.*QBooks|INTUIT.*QUICKBOOKS", True, "Software & Subscriptions", "QuickBooks", 100),
    (r"GAMUT\*|GAMUT\.IO", True, "Software & Subscriptions", "Gamut (Licensing)", 100),
    (r"MANYCHAT", True, "Software & Subscriptions", "ManyChat (Automation)", 100),
    (r"MAIL AUTOMATION|GETMAILTRACKE", True, "Software & Subscriptions", "Mail Automation Inc.", 100),
    (r"PADDLE\.NET.*N8N|PADDLE.*N8N", True, "Software & Subscriptions", "n8n Cloud", 100),
    (r"PADDLE\.NET.*DISKDRILL", True, "Software & Subscriptions", "DiskDrill", 100),
    (r"FOUR VISIONS MARKET", True, "Software & Subscriptions", "Four Visions Market", 100),
    (r"BEATPORT", True, "Software & Subscriptions", "Beatport (Music)", 100),
    # ── 100% Business — Equipment (camera gear, drones) ──────────────────────
    (r"CAMERACANAD", True, "Equipment (CCA)", "Camera Canada", 100),
    (r"DJI", True, "Equipment (CCA)", "DJI (Drone Equipment)", 100),
    # ── 100% Business — Advertising & Marketing ───────────────────────────────
    (r"RESIDENT ADVISOR", True, "Advertising & Marketing", "Resident Advisor (Networking)", 100),
    # ── 100% Business — Rent / Co-working ────────────────────────────────────
    (r"SQ \*FILI SPACE|FILI SPACE", True, "Rent / Co-working", "Fili Space (Co-working)", 100),
    # ── 100% Business — Vehicle & Transport ──────────────────────────────────
    (r"OTTER CO-OP", True, "Vehicle", "Otter Co-op (Gas)", 100),
    (r"PETRO-CANADA", True, "Vehicle", "Petro-Canada (Gas)", 100),
    (r"CHEVRON", True, "Vehicle", "Chevron (Gas)", 100),
    (r"SHELL C\d", True, "Vehicle", "Shell (Gas)", 100),
    (r"SQUAMISH VALLEY GAS", True, "Vehicle", "Squamish Valley Gas", 100),
    (r"PRINCETON ESSO", True, "Vehicle", "Princeton Esso (Gas)", 100),
    (r"CHV\d+", True, "Vehicle", "Chevron (Gas)", 100),   # CHV43005, CHV43019, etc.
    (r"ESSO SMART STOP|ESSO JAI", True, "Vehicle", "Esso (Gas)", 100),
    (r"CANCO PETROLEUM", True, "Vehicle", "Canco Petroleum (Gas)", 100),
    (r"MOBIL@", True, "Vehicle", "Mobil (Gas)", 100),
    (r"AIR-SERV", True, "Vehicle", "Air-Serv (Tire Inflation)", 100),
    (r"VILLAGE PARKING", True, "Vehicle", "Village Parking (Whistler)", 100),
    (r"GREAT CANADIAN OIL CHANGE", True, "Vehicle", "Great Canadian Oil Change", 100),
    # ── 100% Business — Taxes ─────────────────────────────────────────────────
    (r"PAYSIMPLY.*CRA|CRA TAXES", True, "Taxes", "CRA Tax Payment", 100),
    (r"INTUIT.*TURBOTAX", True, "Software & Subscriptions", "TurboTax", 100),
    (r"ANNUAL FEE", True, "Interest & Bank Charges", "Visa Annual Fee", 100),
    (r"PURCHASE INTEREST", True, "Interest & Bank Charges", "Credit Card Interest", 100),
    # ── 50% Business — Software ───────────────────────────────────────────────
    (r"APPLE\.COM/BILL|APPLE\.COM BILL", True, "Software & Subscriptions", "Apple iCloud (50%)", 50),
    # ── Personal — Streaming & Subscriptions ─────────────────────────────────
    (r"Spotify", False, "Subscriptions", "Spotify", 0),
    (r"Netflix", False, "Subscriptions", "Netflix", 0),
    (r"Ad free for PrimeVideo|PrimeVideo", False, "Subscriptions", "Amazon Prime Video", 0),
    (r"Amazon\.ca Prime Member", False, "Software & Subscriptions", "Amazon Prime (Business)", 100),
    # ── Personal — Health & Fitness ───────────────────────────────────────────
    (r"CLIMB GROUNDUP", False, "Health & Fitness", "Climb Groundup (Gym)", 0),
    (r"Scandinave Spa", False, "Health & Fitness", "Scandinave Spa", 0),
    (r"MEC MOUNTAIN EQUIPMENT", False, "Health & Fitness", "MEC", 0),
    (r"SP CLIMB ON EQUIPMENT|LS CLIMB ON", False, "Health & Fitness", "Climb On Equipment", 0),
    (r"BODY ENERGY CLUB", False, "Health & Fitness", "Body Energy Club", 0),
    # ── Personal — Dining Out ─────────────────────────────────────────────────
    (r"TIM HORTONS", False, "Dining Out", "Tim Hortons", 0),
    (r"STARBUCKS", False, "Dining Out", "Starbucks", 0),
    (r"SQ \*THE BUVETTE|THE BUVETTE|BUVETTE", False, "Dining Out", "The Buvette", 0),
    (r"SQ \*TRICKSTER|TRICKSTER", False, "Dining Out", "Trickster's Hideout", 0),
    (r"SQ \*CLOUDBURST|CLOUDBURST", False, "Dining Out", "Cloudburst Cafe", 0),
    (r"SQ \*SUNNY CHIBAS|SUNNY CHIBAS", False, "Dining Out", "Sunny Chibas", 0),
    (r"SQ \*LOCAVORE|LOCAVORE", False, "Dining Out", "Locavore Bar & Grill", 0),
    (r"SQ \*FOX & OAK|FOX & OAK", False, "Dining Out", "Fox & Oak", 0),
    (r"SQ \*FC FUNCTION|FC FUNCTION", False, "Dining Out", "FC Function (Whistler)", 0),
    (r"RAMEN BUTCHER", False, "Dining Out", "Ramen Butcher", 0),
    (r"NOODLEBOX", False, "Dining Out", "Noodlebox", 0),
    (r"DOMINOS|DOMINO", False, "Dining Out", "Domino's", 0),
    (r"PUREBREAD|SQ \*PUREBREAD", False, "Dining Out", "Purebread Bakery", 0),
    (r"BAR BURRITO|BARBURRITO", False, "Dining Out", "Barburrito", 0),
    (r"ESSENCE OF INDIA", False, "Dining Out", "Essence of India", 0),
    (r"TAKA RAMEN", False, "Dining Out", "Taka Ramen & Sushi", 0),
    (r"GINGER SUSHI", False, "Dining Out", "Ginger Sushi", 0),
    (r"A&W", False, "Dining Out", "A&W", 0),
    (r"SAL Y LIMON", False, "Dining Out", "Sal y Limon", 0),
    (r"PICK THAI", False, "Dining Out", "Pick Thai", 0),
    (r"THE NAAM", False, "Dining Out", "The Naam", 0),
    (r"SEA TO SKY HOTEL", False, "Dining Out", "Sea to Sky Hotel (Food)", 0),
    (r"PLATFORM 7", False, "Dining Out", "Platform 7", 0),
    (r"THE FLYING SAGE", False, "Dining Out", "The Flying Sage", 0),
    (r"WATERSHED GRILL", False, "Dining Out", "Watershed Grill", 0),
    (r"CLEVELAND MEATS", False, "Dining Out", "Cleveland Meats", 0),
    (r"TACOS LA CANTINA|LA CANTINA", False, "Dining Out", "La Cantina", 0),
    (r"MOUNT CURRIE COFFEE", False, "Dining Out", "Mount Currie Coffee", 0),
    (r"Mile One Eating", False, "Dining Out", "Mile One Eating House", 0),
    (r"MIRAAS RESTAURANT", False, "Dining Out", "Miraas Restaurant", 0),
    (r"FLAMING WOK", False, "Dining Out", "Flaming Wok", 0),
    (r"SQ \*THE CRABAPPLE|CRABAPPLE CAFE", False, "Dining Out", "Crabapple Cafe", 0),
    (r"Buddha 2", False, "Dining Out", "Buddha 2 Northwoods", 0),
    (r"CAFFE GARIBALDI", False, "Dining Out", "Caffe Garibaldi", 0),
    (r"DILLI HEIGHTS", False, "Dining Out", "Dilli Heights Bistro", 0),
    (r"FIRE PIZZA", False, "Dining Out", "Fire Pizza", 0),
    (r"FLIPSIDE BURGER", False, "Dining Out", "Flipside Burger", 0),
    (r"HARU FUSION", False, "Dining Out", "Haru Fusion Cuisine", 0),
    (r"KING TAPS", False, "Dining Out", "King Taps", 0),
    (r"MANPUKU", False, "Dining Out", "Manpuku", 0),
    (r"NOSHY", False, "Dining Out", "Noshy", 0),
    (r"OPA!|OPA #", False, "Dining Out", "Opa!", 0),
    (r"PELICANA CHICKEN", False, "Dining Out", "Pelicana Chicken", 0),
    (r"PEPE AND GRINGOS", False, "Dining Out", "Pepe and Gringos", 0),
    (r"CACTUS CLUB", False, "Dining Out", "Cactus Club", 0),
    (r"DRAGONBOAT PUB", False, "Dining Out", "Dragonboat Pub", 0),
    (r"BEAN AROUND THE WORLD", False, "Dining Out", "Bean Around the World", 0),
    (r"COCO CAFE", False, "Dining Out", "Coco Cafe", 0),
    (r"CORA ", False, "Dining Out", "Cora", 0),
    (r"C MARKET COFFEE", False, "Dining Out", "C Market Coffee", 0),
    (r"Cranked Espresso", False, "Dining Out", "Cranked Espresso", 0),
    (r"Hunter Gather", False, "Dining Out", "Hunter Gather Eatery", 0),
    (r"Matchstick Fraser", False, "Dining Out", "Matchstick Coffee", 0),
    (r"BUGWOOD BEAN", False, "Dining Out", "Bugwood Bean", 0),
    (r"FRESHSLICE PIZZA", False, "Dining Out", "Freshslice Pizza", 0),
    (r"HIGHWAY TRIPLE O", False, "Dining Out", "Triple O's", 0),
    (r"HARA SUSHI", False, "Dining Out", "Hara Sushi", 0),
    (r"PEAK PROVISIONS", False, "Dining Out", "Peak Provisions", 0),
    (r"BILLIES HOUSE", False, "Dining Out", "Billie's House", 0),
    (r"MUM'S THE WORD", False, "Dining Out", "Mum's the Word", 0),
    (r"FOUNTAIN FLAT TRADING", False, "Dining Out", "Fountain Flat Trading", 0),
    (r"MISSION MERCHANTS", False, "Dining Out", "Mission Merchants", 0),
    (r"SUN DOGS EATERY", False, "Dining Out", "Sun Dogs Eatery", 0),
    (r"BLUE MOOSE COFFEE", False, "Dining Out", "Blue Moose Coffee", 0),
    (r"STRANGE FELLOWS", False, "Dining Out", "Strange Fellows Brewing", 0),
    (r"Ridehub", False, "Dining Out", "Ridehub", 0),
    (r"ARTIGIANO", False, "Dining Out", "Artigiano", 0),
    (r"TOWN SQUARE PEMBERTON", False, "Dining Out", "Town Square (Pemberton)", 0),
    (r"WESTOAK RESTAURANT", False, "Dining Out", "Westoak Restaurant", 0),
    (r"TREE HOUSE CAFE", False, "Dining Out", "Tree House Cafe", 0),
    (r"ABBOTT ST", False, "Dining Out", "Abbott St. Cafe", 0),
    (r"SQ \*BLACKSMITH BAKERY|BLACKSMITH BAKERY", False, "Dining Out", "Blacksmith Bakery", 0),
    (r"GROUNDS FOR COFFEE", False, "Dining Out", "Grounds for Coffee", 0),
    (r"BODY ENERGY", False, "Dining Out", "Body Energy Club", 0),
    (r"THE GUMBOOT CAFE|GUMBOOT", False, "Dining Out", "Gumboot Cafe", 0),
    (r"MEDITERRANEAN GRILL|MEDITERRANEAN", False, "Dining Out", "Mediterranean Grill", 0),
    (r"SQ \*THE BRASS SPOON|BRASS SPOON", False, "Dining Out", "The Brass Spoon Cafe", 0),
    (r"SQ \*THE BUNKER|BUNKER CAFE", False, "Dining Out", "The Bunker Cafe", 0),
    (r"TST-|SQ \*ALPHA CAFE|SQ \*BRACKENDALE|SQ \*IL MUNDO|SQ \*MIRAAS|SQ \*OLDHAND|SQ \*OUTBOUND|SQ \*PERSEPHONE|SQ \*SMOKE BLUFF|SQ \*STILLFOOD|SQ \*STOKED|SQ \*SUPERBABA|SQ \*SWEET THEA|SQ \*TEXAS SMOKE|SQ \*THE BRACKENDALE|SQ \*TREE HOUSE|SQ \*TURKS|SQ \*WAYNE|SQ \*A-FRAME BREWING|SQ \*ALICE AND BROHM|SQ \*BLUEPRINT EVENTS|SQ \*BRIGHT JENNY|SQ \*DIGITAL MOTION|SQ \*INDUSTRIAL|SQ \*JJ BEAN|SQ \*SALT SPRING|SQ \*SULA", False, "Dining Out", "Cafe / Restaurant", 0),
    (r"SQ \*THE PALM", False, "Dining Out", "The Palm", 0),
    (r"RED ROOM ULTRABAR", False, "Entertainment", "Red Room Ultrabar", 0),
    # ── Personal — Groceries ──────────────────────────────────────────────────
    (r"HECTOR'S YOUR INDEPEND|HECTOR", False, "Groceries", "Hector's (Grocery)", 0),
    (r"NESTERS", False, "Groceries", "Nesters Market", 0),
    (r"LONDON DRUGS", False, "Groceries", "London Drugs", 0),
    (r"REAL CDN SUPERSTORE|REAL CDN\. SUPERSTORE", False, "Groceries", "Real Canadian Superstore", 0),
    (r"SAVE ON FOODS", False, "Groceries", "Save-On-Foods", 0),
    (r"SAFEWAY", False, "Groceries", "Safeway", 0),
    (r"WHOLE FOODS", False, "Groceries", "Whole Foods Market", 0),
    (r"THRIFTY FOODS", False, "Groceries", "Thrifty Foods", 0),
    (r"SANDERSON FRUIT STAND", False, "Groceries", "Sanderson Fruit Stand", 0),
    (r"VILLAGE FOOD MARKETS", False, "Groceries", "Village Food Markets", 0),
    (r"FRESH ST\. MARKET", False, "Groceries", "Fresh St. Market", 0),
    (r"IGA \d", False, "Groceries", "IGA", 0),
    (r"BUY LOW FOODS", False, "Groceries", "Buy Low Foods", 0),
    (r"GREEN OLIVE MARKET", False, "Groceries", "Green Olive Market", 0),
    (r"DONALDS MARKET", False, "Groceries", "Donalds Market", 0),
    (r"PEAK PROVISIONS", False, "Groceries", "Peak Provisions", 0),
    (r"CPC / SCP", False, "Groceries", "Co-op Grocery", 0),
    # ── Personal — Entertainment / Events ─────────────────────────────────────
    (r"SHAMBHALA|SHAMBHALA\*", False, "Entertainment", "Shambhala Music Festival", 0),
    (r"TICKETMASTER", False, "Entertainment", "Ticketmaster", 0),
    (r"TCKTWEB", False, "Entertainment", "Event Ticket", 0),
    (r"SEA TO SKY GONDOLA", False, "Entertainment", "Sea to Sky Gondola", 0),
    (r"Beltane Fire Festival", False, "Entertainment", "Beltane Fire Festival", 0),
    (r"DOME PLANETARIUM", False, "Entertainment", "HR MacMillan Planetarium", 0),
    (r"CINEPLEX", False, "Entertainment", "Cineplex", 0),
    (r"EVENTBRITE", False, "Entertainment", "Eventbrite", 0),
    # ── Personal — Retail & Shopping ─────────────────────────────────────────
    (r"APPLE STORE", False, "Personal Shopping", "Apple Store", 0),
    (r"WAL-MART|WALMART", False, "Personal Shopping", "Walmart", 0),
    (r"MARKS SQUAMISH|#829 MARKS", False, "Personal Shopping", "Mark's Work Wearhouse", 0),
    (r"SP DU/ER", False, "Personal Shopping", "Du/er Clothing", 0),
    (r"RANDOM & CO", False, "Personal Shopping", "Random & Co", 0),
    (r"7 ELEVEN|7-ELEVEN", False, "Personal Shopping", "7-Eleven", 0),
    (r"HOME DEPOT", False, "Personal Shopping", "Home Depot", 0),
    (r"RONA", False, "Personal Shopping", "RONA", 0),
    (r"RX DRUG MART", False, "Health & Fitness", "Rx Drug Mart (Pharmacy)", 0),
    (r"SQUAMISH SOURCE FOR SPORT", False, "Personal Shopping", "Source for Sports", 0),
    (r"CANADIAN TIRE", False, "Personal Shopping", "Canadian Tire", 0),
    (r"CREATIVE STITCHES", False, "Personal Shopping", "Creative Stitches", 0),
    (r"DOLLARAMA", False, "Personal Shopping", "Dollarama", 0),
    (r"MICHAELS", False, "Personal Shopping", "Michaels", 0),
    (r"BOSLEYS|PET VALU", False, "Personal Shopping", "Bosleys / Pet Valu", 0),
    (r"BE CLEAN NATURALLY", False, "Personal Shopping", "Be Clean Naturally", 0),
    # ── Personal — Liquor ─────────────────────────────────────────────────────
    (r"BC LIQUOR|SQUAMISH LIQUOR|TWIN VALLEY LIQUOR|ARC LIQUOR|SIDNEY COLD BEER|VOYAGE LIQUOR", False, "Dining Out", "Liquor Store", 0),
    # ── Personal — Telecom ────────────────────────────────────────────────────
    (r"ROGERS", False, "Telephone & Internet", "Rogers (Phone)", 0),
    # ── Personal — Transport ──────────────────────────────────────────────────
    (r"BCF -|BCF -.*VICTORIA|BC FERRIES", False, "Transportation", "BC Ferries", 0),
    (r"BLACK TOP.*CABS|TAXI|UBER|LYFT", False, "Transportation", "Taxi / Rideshare", 0),
    (r"BLACK TOP", False, "Transportation", "Black Top Cab", 0),
    (r"EASYPARK|HONK PARKING|IMPARK|PAY PARKING|CITY OF VANCOUVER PARKING", False, "Transportation", "Parking", 0),
    # ── Personal — Government ─────────────────────────────────────────────────
    (r"TRANSPORTSCANADA", False, "Government Fees", "Transport Canada", 0),
    (r"ANNUAL REBATE FEE", False, "Interest & Bank Charges", "Visa Rebate Fee", 0),
    (r"PAYBACK WITH POINTS", False, "Interest & Bank Charges", "Points Redemption", 0),
    # ── Personal — Other ─────────────────────────────────────────────────────
    (r"UPS\*", False, "Shipping", "UPS", 0),
    (r"Afterpay", False, "Personal Shopping", "Afterpay", 0),
]


def categorize(desc, amount):
    """Return (is_business, category, clean_name, split_pct)."""
    for pattern, is_biz, cat, name, split in RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            # Amazon: business if <$500 → Office Supplies, ≥$500 → Equipment
            if re.search(r"AMAZON", name, re.IGNORECASE) and is_biz:
                if abs(amount) >= 500:
                    return True, "Equipment (CCA)", name, split
            return is_biz, cat, name, split

    # Fallback — check for known patterns in raw desc
    if re.search(r"AMAZON|AMZN", desc, re.IGNORECASE):
        if abs(amount) >= 500:
            return True, "Equipment (CCA)", "Amazon (Equipment)", 100
        return True, "Office Supplies (<$500)", "Amazon (Supplies)", 100

    # Default: flag as uncategorized for review
    clean = re.sub(r"\s{2,}", " ", desc).strip()[:35]
    return False, "Uncategorized", clean, 0


def calc_gst(amount):
    return round(abs(amount) / 1.05 * 0.05, 2)


def main():
    svc = get_sheets_service()

    # ── Find last populated row in Transactions tab ───────────────────────────
    result = svc.spreadsheets().values().get(
        spreadsheetId=SHEET_ID,
        range="Transactions!A4:A2000"
    ).execute()
    values = result.get("values", [])
    # Row 4 is headers; count populated rows after that
    last_data_row = 4 + len(values)  # 1-indexed sheet row of last row with data
    next_row = last_data_row + 1

    # If this is a re-run, clear any existing personal Visa rows first
    # (identified by Account column = "Personal Card")
    # We do this by reading and finding the start point
    print(f"Last populated row: {last_data_row}  →  Appending from row {next_row}")

    # ── Parse CSV ─────────────────────────────────────────────────────────────
    rows = []
    skipped_payments = 0
    skipped_no_amount = 0

    with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            amt_str = row.get("CAD$", "").strip()
            if not amt_str:
                skipped_no_amount += 1
                continue

            amount = float(amt_str)
            desc1 = row.get("Description 1", "").strip()
            desc2 = row.get("Description 2", "").strip()
            desc = f"{desc1} {desc2}".strip()
            date_raw = row.get("Transaction Date", "").strip()

            # Skip card payments (positive, "PAYMENT" in description)
            if amount > 0 and "PAYMENT" in desc.upper():
                skipped_payments += 1
                continue

            is_biz, cat, name, split_pct = categorize(desc, amount)

            if split_pct == 50 and amount < 0:
                # Single row approach: record as business with 50% split
                gst = calc_gst(amount / 2)
                rows.append([
                    date_raw,
                    name,
                    desc[:50],
                    amount,
                    True,
                    cat,
                    "50%",
                    gst,
                    False,
                    "Visa",
                    "Personal Card",
                    "50% business / 50% personal"
                ])
            else:
                gst = calc_gst(amount) if is_biz and amount < 0 else 0
                pct_str = f"{split_pct}%" if is_biz else "0%"
                rows.append([
                    date_raw,
                    name,
                    desc[:50],
                    amount,
                    is_biz,
                    cat,
                    pct_str,
                    gst,
                    False,
                    "Visa",
                    "Personal Card",
                    ""
                ])

    # Sort chronologically
    def parse_date(r):
        try:
            return datetime.strptime(r[0], "%m/%d/%Y")
        except ValueError:
            return datetime.min

    rows.sort(key=parse_date)

    print(f"Parsed {len(rows)} transactions (skipped {skipped_payments} payments, {skipped_no_amount} no-amount rows)")

    # ── Write to sheet ─────────────────────────────────────────────────────────
    if not rows:
        print("No rows to write.")
        return

    svc.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f"Transactions!A{next_row}:L{next_row + len(rows) - 1}",
        valueInputOption="USER_ENTERED",
        body={"values": rows}
    ).execute()

    print(f"Written {len(rows)} rows to Transactions tab (rows {next_row}–{next_row + len(rows) - 1})")

    # ── Summary ────────────────────────────────────────────────────────────────
    biz_rows = [r for r in rows if r[4] is True and r[3] < 0]
    pers_rows = [r for r in rows if r[4] is False and r[3] < 0]
    refund_rows = [r for r in rows if r[3] > 0]

    biz_total = sum(abs(r[3]) for r in biz_rows)
    # For 50% rows, actual business portion is half
    biz_actual = 0
    for r in biz_rows:
        if r[6] == "50%":
            biz_actual += abs(r[3]) * 0.5
        else:
            biz_actual += abs(r[3])

    pers_total = sum(abs(r[3]) for r in pers_rows)
    gst_itc = sum(r[7] for r in biz_rows)
    refund_total = sum(r[3] for r in refund_rows)

    print(f"\n{'═'*50}")
    print(f"  PERSONAL VISA •1351 — IMPORT SUMMARY")
    print(f"{'═'*50}")
    print(f"  Transactions added:      {len(rows)}")
    print(f"  Business expenses (gross): ${biz_total:,.2f}")
    print(f"  Business expenses (net 50%):${biz_actual:,.2f}")
    print(f"  Personal expenses:       ${pers_total:,.2f}")
    print(f"  Refunds / credits:       ${refund_total:,.2f}")
    print(f"  GST ITCs:                ${gst_itc:,.2f}")

    # Category breakdown
    cats = {}
    for r in biz_rows:
        portion = abs(r[3]) * 0.5 if r[6] == "50%" else abs(r[3])
        cats[r[5]] = cats.get(r[5], 0) + portion
    print(f"\n  Business categories:")
    for cat, amt in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"    {cat:<35} ${amt:,.2f}")

    # Top 10 vendors by spend (gross)
    vendors = {}
    for r in rows:
        if r[3] < 0:
            vendors[r[1]] = vendors.get(r[1], 0) + abs(r[3])
    top10 = sorted(vendors.items(), key=lambda x: -x[1])[:10]
    print(f"\n  Top 10 vendors by spend:")
    for i, (vendor, amt) in enumerate(top10, 1):
        print(f"    {i:2}. {vendor:<35} ${amt:,.2f}")

    # Uncategorized rows for review
    uncat = [r for r in rows if r[5] == "Uncategorized"]
    if uncat:
        print(f"\n  ⚠  Uncategorized ({len(uncat)} rows) — review needed:")
        for r in uncat[:20]:
            print(f"    {r[0]}  {r[2][:50]}  ${r[3]:.2f}")


if __name__ == "__main__":
    main()
