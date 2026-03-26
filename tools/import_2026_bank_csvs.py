"""
Import 4 bank CSVs into 2026 Finance Sheet.
- Parse all CSVs, categorize, skip payments/transfers
- Write INCOME and EXPENSES sections
- Apply formatting, checkboxes, dropdowns, month helper
- Print summary stats
"""
import sys, os, csv, re, time
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service

SHEET_ID = '1fPpOPnAYEnfCu33h1ki9NzFGTUOkpgd4mMSQX_sT9CY'
CUTOFF = datetime(2026, 3, 20)

# Date serial: days since Dec 30, 1899
def date_serial(dt):
    base = datetime(1899, 12, 30)
    return (dt - base).days

def parse_date(s):
    """Parse M/D/YYYY"""
    parts = s.strip().split('/')
    return datetime(int(parts[2]), int(parts[0]), int(parts[1]))

def clean_vendor(desc):
    """Extract clean vendor name from description."""
    d = desc.strip()
    # Remove common suffixes
    d = re.sub(r'\s+(VANCOUVER|SQUAMISH|GARIBALDI HIG|NORTH VANCOUV|N\.VANCOUVER|RICHMOND|BURNABY|TORONTO|Stockholm|PARIS|PRAGUE|SINGAPORE|INTERNET|WILMINGTON|CALGARY|BADUNG.*|GIANYAR.*|South Jakarta|KUALALUMPUR|COLOMBO|KATUNAYAKE|BATTARAMULLA|BATTARMULLA|AHANGAMA|WELIGAMA|DIKWELLA|THALAWATHUGOD|CHEKLAPKOK|Hong Kong|San Jose|WEST VANCOUVE|Brackendale|GARIBALDIHIGH|SEPANG)$', '', d, flags=re.IGNORECASE).strip()
    # Remove transaction IDs
    d = re.sub(r'\s*\*\s*[A-Z0-9]{8,}\s*', ' ', d).strip()
    d = re.sub(r'\s+[A-Z0-9]{6,}$', '', d).strip()
    # Clean common patterns
    d = re.sub(r'\s+\d{3}-\d{3}-\d{4}$', '', d).strip()
    d = re.sub(r'\s+\d{3}-\d{7}$', '', d).strip()
    d = re.sub(r'\s+www\.\S+', '', d, flags=re.IGNORECASE).strip()
    d = re.sub(r'\s+CC\s+GOOGLE\.COM', '', d).strip()
    d = re.sub(r'\s+Amzn\.com/bill', '', d, flags=re.IGNORECASE).strip()
    d = re.sub(r'PAYMENT - THANK YOU.*', 'PAYMENT', d).strip()
    d = re.sub(r'MISC PAYMENT ', '', d).strip()
    d = re.sub(r'^\d+_', '', d).strip()
    # Remove foreign currency info
    d = re.sub(r'\s*\d[\d,.]+\s*(IDR|LKR|USD|TWD|MYR|HKD|EUR)\s*@\s*[\d.]+', '', d).strip()
    # Title case cleanup
    if d.isupper() and len(d) > 3:
        # Keep as-is for acronyms and brands
        pass
    return d[:40]

def truncate_desc(desc, n=40):
    d = desc.strip()
    if len(d) > n:
        d = d[:n-1] + '…'
    return d

# ── Squamish restaurants/cafes for personal dining detection ──
SQUAMISH_DINING = [
    'BACKCOUNTRY BREWING', 'BARBURRITO', 'DOMINOS', 'PUREBREAD', 'CRABAPPLE',
    'CLOUDBURST', 'FOX & OAK', 'NOODLEBOX', 'ESSENCE OF INDIA', 'SEA TO SKY HOTEL',
    'BRACKENDALE ART', 'SUSHI SEN', 'IL MUNDO'
]
VANCOUVER_DINING = [
    'RAMEN BUTCHER', 'DEVILLE COFFEE', 'TRAFIQ CAFE', 'CONTINENTAL COFFEE', 'CHAI RESTAURANTS',
    'STARBUCKS', 'SUBWAY'
]

# ── Categorization Engine ──
def categorize(desc, amount, account, desc2=''):
    """
    Returns (business: bool, category: str, split: str, notes: str, vendor_clean: str, skip: bool)
    """
    d = (desc + ' ' + desc2).upper()
    amt = float(amount) if amount else 0
    vendor = clean_vendor(desc + ' ' + desc2)

    # ── SKIP RULES ──
    # Card payments (positive + PAYMENT in description)
    if amt > 0 and 'PAYMENT' in d and ('THANK YOU' in d or 'MERCI' in d):
        return None, None, None, None, vendor, True
    # Internal bank transfers
    if 'ONLINE BANKING TRANSFER' in d:
        return None, None, None, None, vendor, True
    # E-transfer to self
    if 'E-TRANSFER SENT MATTHEW FERNANDES' in d:
        return None, None, None, None, vendor, True
    # PLUS surcharges (ATM fees already in withdrawal)
    if d.startswith('PLUS - SC'):
        return None, None, None, None, vendor, True
    # Olga Lissey sent (e-transfer to Olga)
    if 'E-TRANSFER SENT OLGA LISSEY' in d:
        return False, 'Other Personal', '0%', 'E-transfer to Olga Lissey', 'Olga Lissey', False
    # Rogers payment from chequing (duplicate of card charge)
    if 'ONLINE BANKING PAYMENT' in d and 'ROGERS' in d:
        return None, None, None, None, vendor, True

    # ── INCOME ──
    if 'STRIPE' in d and amt > 0:
        return True, 'Stripe (Revenue)', '100%', 'Client payment via Stripe', 'Stripe', False
    if 'E-TRANSFER RECEIVED' in d and amt > 0:
        # Olga Lissey = personal (damage deposit return)
        if 'OLGA LISSEY' in d:
            return False, 'Other Personal', '0%', 'Damage deposit return from Olga Lissey', 'Olga Lissey', False
        # Self transfer from business account
        if 'MATTHEW' in d and 'FERNANDES' in d:
            return None, None, None, None, vendor, True  # self-transfer, skip
        return True, 'Business Income', '100%', 'Client e-transfer payment', vendor, False
    if 'MOBILE CHEQUE DEPOSIT' in d and amt > 0:
        return True, 'Business Income', '100%', 'Client cheque deposit', vendor, False
    if 'GST CANADA' in d or 'GST/HST CREDIT' in d:
        return False, 'Other Personal', '0%', 'Government GST credit', 'CRA - GST', False
    if 'CANADA WORKERS BENEFIT' in d:
        return False, 'Other Personal', '0%', 'Canada Workers Benefit', 'CRA - CWB', False

    # ── REFUNDS (positive amounts from specific vendors → expense credits) ──
    if amt > 0 and ('AMAZON' in d or 'ADOBE' in d or 'MEC' in d or 'MOUNTAIN EQUIPMENT' in d):
        # These are refunds, categorize as expense credits
        if 'ADOBE' in d:
            return True, 'Software & Subscriptions', '100%', 'Adobe refund/credit', 'Adobe', False
        if 'MOUNTAIN EQUIPMENT' in d or 'MEC' in d:
            return False, 'Other Personal', '0%', 'MEC refund', 'MEC', False
        # Amazon refund
        if account == 'Business Card':
            return True, 'Office Supplies (<$500)', '100%', 'Amazon refund/credit', 'Amazon', False
        return False, 'Other Personal', '0%', 'Amazon refund', 'Amazon', False

    # ── AFFIRM (camera gear financing) ──
    if 'AFFIRM' in d:
        return True, 'Equipment (CCA)', '100%', 'Camera gear financing payment (Affirm)', 'Affirm', False

    # ── 100% BUSINESS EXPENSES ──
    # Software & Subscriptions
    if 'GOOGLE' in d and ('WORKSPACE' in d or 'GSUITE' in d):
        return True, 'Software & Subscriptions', '100%', 'Google Workspace business email/storage', 'Google Workspace', False
    if 'ADOBE' in d:
        return True, 'Software & Subscriptions', '100%', 'Adobe Creative Cloud for photo editing', 'Adobe', False
    if 'INSTANTLY' in d:
        return True, 'Software & Subscriptions', '100%', 'Instantly.ai cold email outreach platform', 'Instantly', False
    if 'BUFFER' in d:
        return True, 'Software & Subscriptions', '100%', 'Buffer social media scheduling', 'Buffer', False
    if 'OPENROUTER' in d:
        return True, 'Software & Subscriptions', '100%', 'OpenRouter AI API for business automation', 'OpenRouter', False
    if 'LEADGENJAY' in d:
        return True, 'Software & Subscriptions', '100%', 'LeadGenJay lead generation service', 'LeadGenJay', False
    if 'APIFY' in d:
        return True, 'Software & Subscriptions', '100%', 'Apify web scraping for lead gen', 'Apify', False
    if 'CLICKUP' in d:
        return True, 'Software & Subscriptions', '100%', 'ClickUp project management', 'ClickUp', False
    if 'EPIDEMIC SOUND' in d or 'EPIDEMICSOUND' in d:
        return True, 'Software & Subscriptions', '100%', 'Epidemic Sound music licensing for video', 'Epidemic Sound', False
    if 'DROPBOX' in d:
        return True, 'Software & Subscriptions', '100%', 'Dropbox cloud storage for client deliverables', 'Dropbox', False
    if 'QUICKBOOKS' in d or 'INTUIT' in d and 'QBOOKS' in d:
        return True, 'Software & Subscriptions', '100%', 'QuickBooks accounting software', 'QuickBooks', False
    if 'HIGHLEVEL' in d or 'GOHIGHLEVEL' in d:
        return True, 'Software & Subscriptions', '100%', 'GoHighLevel CRM for client management', 'GoHighLevel', False
    if 'ICYPEAS' in d:
        return True, 'Software & Subscriptions', '100%', 'Icypeas email verification for outreach', 'Icypeas', False
    if 'OPENAI' in d or 'CHATGPT' in d:
        return True, 'Software & Subscriptions', '100%', 'OpenAI/ChatGPT for business content & automation', 'OpenAI', False
    if 'AUDIBLE' in d:
        return True, 'Software & Subscriptions', '100%', 'Audible business/professional development books', 'Audible', False
    if 'EXPRESSVPN' in d:
        return True, 'Software & Subscriptions', '100%', 'ExpressVPN for secure client data access', 'ExpressVPN', False
    if 'HOSTINGER' in d:
        return True, 'Software & Subscriptions', '100%', 'Hostinger web hosting for business website', 'Hostinger', False
    if 'KINDLE' in d:
        return True, 'Software & Subscriptions', '100%', 'Kindle business/professional development books', 'Kindle', False
    if 'N8N' in d or 'PADDLE' in d:
        return True, 'Software & Subscriptions', '100%', 'n8n workflow automation platform', 'n8n', False
    if 'AMAZON PRIME' in d or 'PRIMEVIDEO' in d or 'PRIME VIDEO' in d:
        return True, 'Software & Subscriptions', '100%', 'Amazon Prime for business shipping & reference', 'Amazon Prime', False

    # Advertising & Marketing
    if 'SHOWPASS' in d:
        return True, 'Advertising & Marketing', '100%', 'Showpass event marketing/networking', 'Showpass', False
    if 'FACEBOOK' in d or 'FACEBK' in d:
        return True, 'Advertising & Marketing', '100%', 'Facebook/Meta advertising', 'Facebook Ads', False

    # Vehicle
    if 'PETRO-CANADA' in d or 'PETRO CANADA' in d:
        return True, 'Vehicle', '100%', 'Fuel for business vehicle', 'Petro-Canada', False
    if 'CHEVRON' in d:
        return True, 'Vehicle', '100%', 'Fuel for business vehicle', 'Chevron', False
    if 'SHELL' in d and 'SHELL' in desc.upper():
        return True, 'Vehicle', '100%', 'Fuel for business vehicle', 'Shell', False
    if 'ESSO' in d:
        return True, 'Vehicle', '100%', 'Fuel for business vehicle', 'Esso', False
    if 'EASYPARK' in d or 'PARKING' in d or 'VILLAGE PARKING' in d:
        return True, 'Vehicle', '100%', 'Parking for client site visit', 'Parking', False
    if 'BC FERRIES' in d:
        return True, 'Vehicle', '100%', 'BC Ferries for client site travel', 'BC Ferries', False
    if 'WESTMOUNT CHE' in d or ('CHV' in d and 'CHE' in d):
        return True, 'Vehicle', '100%', 'Fuel for business vehicle', 'Chevron', False
    if 'AIR-SERV' in d:
        return True, 'Vehicle', '100%', 'Vehicle air/maintenance', 'Air-Serv', False

    # Interest & Bank Charges
    if 'MONTHLY FEE' in d or 'ANNUAL FEE' in d:
        return True, 'Interest & Bank Charges', '100%', 'Monthly bank account fee', 'Bank Fee', False
    if 'LOAN INTEREST' in d:
        return True, 'Interest & Bank Charges', '100%', 'Business loan interest', 'Loan Interest', False
    if 'PURCHASE INTEREST' in d:
        return True, 'Interest & Bank Charges', '100%', 'Credit card interest charge', 'Card Interest', False

    # Telephone & Internet
    if 'ROGERS' in d:
        return True, 'Telephone & Internet', '100%', 'Rogers phone/internet for business communication', 'Rogers', False

    # Rent / Co-working
    if 'OUTPOST LANKA' in d:
        return True, 'Rent / Co-working', '100%', 'Outpost co-working space for remote work', 'Outpost Lanka', False

    # ── BUSINESS WITH SPLIT ──
    if 'ICBC' in d:
        return True, 'Vehicle', '70%', 'ICBC auto insurance (70% business use)', 'ICBC', False
    if 'COOPERATORS' in d:
        return True, 'Insurance', '70%', 'Co-operators insurance (70% business use)', 'Co-operators', False
    if 'AIRBNB' in d:
        return True, 'Travel', '50%', 'Airbnb accommodation during business travel', 'Airbnb', False
    if 'GRAB' in d:
        return True, 'Travel', '50%', 'Grab ride during business travel', 'Grab', False
    if 'AIRASIA' in d or 'AIR ASIA' in d:
        return True, 'Travel', '50%', 'AirAsia flight for business travel', 'AirAsia', False
    if 'CATHAYPAC' in d:
        return True, 'Travel', '50%', 'Cathay Pacific flight for business travel', 'Cathay Pacific', False
    if 'AIRALO' in d:
        return True, 'Travel', '50%', 'Airalo eSIM for business travel connectivity', 'Airalo', False
    if 'ONWARD TICKET' in d:
        return True, 'Travel', '50%', 'Onward ticket for international business travel', 'Onward Ticket', False
    if 'VISA ON ARRIVAL' in d or 'VISAARR' in d or 'DEPT OF IMMIGRATION' in d or 'DEPARTMENT OF IMMIGRATION' in d:
        return True, 'Travel', '50%', 'Visa on arrival for business travel', 'Visa on Arrival', False
    if 'CLEAR POINT WILD FOREST' in d:
        return True, 'Travel', '50%', 'Clear Point Wild Forest accommodation', 'Clear Point Wild Forest', False
    if 'TUGO' in d:
        return True, 'Travel', '50%', 'TuGo travel insurance for business trip', 'TuGo Insurance', False

    # ── AMAZON (amount-based) ──
    if 'AMAZON' in d:
        if account == 'Business Card':
            if abs(amt) >= 500:
                return True, 'Equipment (CCA)', '100%', 'Amazon equipment purchase >$500', 'Amazon', False
            else:
                return True, 'Office Supplies (<$500)', '100%', 'Amazon office/business supplies', 'Amazon', False
        else:
            # Personal card Amazon - likely personal
            if abs(amt) >= 500:
                return True, 'Equipment (CCA)', '100%', 'Amazon equipment purchase >$500', 'Amazon', False
            return False, 'Other Personal', '0%', 'Amazon personal purchase', 'Amazon', False

    # ── HOME DEPOT, CANADIAN TIRE ──
    if 'HOME DEPOT' in d:
        return True, 'Office Supplies (<$500)', '100%', 'Home Depot office/studio supplies', 'Home Depot', False
    if 'CANADIAN TIRE' in d:
        return True, 'Office Supplies (<$500)', '100%', 'Canadian Tire office/studio supplies', 'Canadian Tire', False

    # ── PAYPAL (business tool payment) ──
    if 'PAYPAL' in d:
        return True, 'Software & Subscriptions', '100%', 'PayPal subscription/service payment', 'PayPal', False

    # ── QUESTRADE ──
    if 'QUESTRADE' in d:
        return False, 'Savings/Investments', '0%', 'Questrade investment transfer', 'Questrade', False

    # ── SHAKEPAY ──
    if 'SHAKEPAY' in d:
        return False, 'Savings/Investments', '0%', 'Shakepay crypto purchase', 'Shakepay', False

    # ── RENT (e-transfer) ──
    if 'E-TRANSFER SENT' in d and 'RENT' in d:
        return False, 'Housing', '0%', 'Monthly rent payment', 'Rent', False

    # ── ATM WITHDRAWAL ──
    if 'ATM WITHDRAWAL' in d:
        return False, 'Other Personal', '0%', 'ATM cash withdrawal', 'ATM Withdrawal', False

    # ── PERSONAL ──
    if 'SPOTIFY' in d:
        return False, 'Subscriptions', '0%', 'Spotify music subscription', 'Spotify', False
    if 'APPLE.COM/BILL' in d or 'APPLE.COM' in d:
        return False, 'Subscriptions', '0%', 'Apple subscription', 'Apple', False
    if 'CLIMB GROUNDUP' in d:
        return False, 'Health & Fitness', '0%', 'Climb Groundup gym membership', 'Climb Groundup', False
    if 'UBER' in d:
        return False, 'Transportation', '0%', 'Uber ride', 'Uber', False
    if 'SQUAMISHCONNECTOR' in d or 'COMPASS' in d:
        return False, 'Transportation', '0%', 'Public transit', vendor, False

    # ── DINING (Squamish = personal) ──
    for r in SQUAMISH_DINING:
        if r in d:
            return False, 'Dining Out', '0%', f'Dining in Squamish', vendor, False
    for r in VANCOUVER_DINING:
        if r in d:
            return False, 'Dining Out', '0%', f'Dining in Vancouver', vendor, False

    # ── GROCERIES ──
    if "HECTOR'S" in d or 'HECTORS' in d:
        return False, 'Groceries', '0%', 'Groceries (Hectors)', "Hector's", False
    if 'NESTERS' in d:
        return False, 'Groceries', '0%', 'Groceries (Nesters)', 'Nesters', False
    if 'LONDON DRUGS' in d:
        return False, 'Groceries', '0%', 'London Drugs purchase', 'London Drugs', False
    if 'DOLLARAMA' in d:
        return False, 'Other Personal', '0%', 'Dollarama purchase', 'Dollarama', False
    if 'MARKS' in d and '#829' in d:
        return False, 'Clothing', '0%', "Mark's clothing purchase", "Mark's", False

    # ── Meals outside Squamish (business) ──
    # Bali meals
    bali_places = ['BAKED BATU', 'ZIN CAFE', 'GAYA GELATO', 'SOOGI ROLL', 'NEW AVOCADO',
                   'GOAT FATHER', 'MOTION PERERENAN', 'KAYUNAN', 'RUSTERS', 'CLEAR CAFE',
                   'REVOLVER', 'ALCHEMY CANGGU', 'WHSMITH', 'GIGI SUSU', 'TUGU BALI',
                   'SWAN MART', 'BAMBU FITNESS', 'MISSION YOGA', 'ALCHEMY YOGA']
    for p in bali_places:
        if p in d:
            if 'FITNESS' in p or 'YOGA' in p or 'MISSION YOGA' in p or 'ALCHEMY YOGA' in p:
                return False, 'Health & Fitness', '0%', 'Fitness/yoga class in Bali', vendor, False
            if 'SWAN MART' in p:
                return False, 'Groceries', '0%', 'Grocery shopping in Bali', vendor, False
            if 'TUGU BALI' in p:
                return True, 'Meals & Entertainment', '100%', 'Meal during shoot day — Bali', vendor, False
            return True, 'Meals & Entertainment', '100%', 'Meal during business travel — Bali', vendor, False

    # Sri Lanka meals
    sri_lanka_places = ['PLAN B CAFE', 'STICK SURF', 'LAMANA', 'JAVA LOUNGE',
                        'ZIPPI', 'AHANGAMA DAIRIES', 'H A C PERERA',
                        'SENSES YOGA', 'A4 RESIDENCE']
    for p in sri_lanka_places:
        if p in d:
            if 'YOGA' in p or 'SENSES' in p:
                return False, 'Health & Fitness', '0%', 'Yoga class in Sri Lanka', vendor, False
            if 'A4 RESIDENCE' in p:
                return True, 'Travel', '50%', 'Airport accommodation in Sri Lanka', vendor, False
            return True, 'Meals & Entertainment', '100%', 'Meal during business travel — Sri Lanka', vendor, False

    # Hong Kong / transit meals
    if 'MOON THAI' in d or 'AHH-YUM' in d or 'GORDON' in d:
        return True, 'Meals & Entertainment', '100%', 'Meal during business travel — transit', vendor, False

    # Whistler / other BC
    if 'WHISTLER' in d:
        return True, 'Meals & Entertainment', '100%', 'Meal during shoot day — Whistler', vendor, False

    # Taiwan
    if 'SHEN HENG' in d or 'TAOYUAN' in d:
        return True, 'Meals & Entertainment', '100%', 'Meal during business travel — Taiwan', vendor, False

    # XDT Megatix Indonesia
    if 'MEGATIX' in d:
        return False, 'Entertainment', '0%', 'Event ticket in Indonesia', vendor, False

    # Coastal Crystals, Buddha
    if 'COASTAL CRYSTALS' in d or 'BUDDHA' in d:
        return False, 'Other Personal', '0%', 'Personal purchase', vendor, False

    # City of Vancouver Parking
    if 'CITY OF VANCOUVER PARKING' in d:
        return True, 'Vehicle', '100%', 'Parking for client meeting in Vancouver', 'Parking', False

    # Chai Restaurants (Vancouver dinner — could be client meal)
    if 'CHAI RESTAURANTS' in d:
        return True, 'Meals & Entertainment', '100%', 'Client/networking meal — Vancouver', 'Chai Restaurant', False

    # ── Business Card default ──
    if account == 'Business Card':
        return True, 'Other Business', '100%', 'Business card purchase', vendor, False
    if account == 'Business Chequing':
        return True, 'Other Business', '100%', 'Business chequing transaction', vendor, False

    # ── Fallback: personal ──
    return False, 'Other Personal', '0%', '', vendor, False


def parse_csv(filepath, account_name, payment_method):
    """Parse a bank CSV and return list of transaction dicts."""
    txns = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row.get('Transaction Date', '').strip()
            if not date_str:
                continue
            dt = parse_date(date_str)
            if dt > CUTOFF:
                continue

            desc1 = row.get('Description 1', '').strip()
            desc2 = row.get('Description 2', '').strip()
            amt_str = row.get('CAD$', '').strip().replace(',', '')
            if not amt_str:
                continue
            amt = float(amt_str)

            full_desc = desc1 + (' ' + desc2 if desc2 else '')

            business, category, split, notes, vendor, skip = categorize(
                desc1, amt, account_name, desc2
            )

            if skip:
                continue

            # Calculate GST for business expenses
            gst = ''
            if business and amt < 0:
                split_pct = int(split.replace('%', '')) / 100.0
                gst_amount = round(abs(amt) * split_pct * 5 / 105, 2)
                gst = f'=ROUND(ABS(D{{row}})*VALUE(SUBSTITUTE(G{{row}},"%",""))/100*5/105,2)'
            elif business and amt > 0 and category != 'Stripe (Revenue)' and category != 'Business Income':
                # Refund credits — GST credit
                gst = f'=ROUND(ABS(D{{row}})*VALUE(SUBSTITUTE(G{{row}},"%",""))/100*5/105,2)'

            txns.append({
                'date': dt,
                'date_serial': date_serial(dt),
                'vendor': vendor,
                'description': truncate_desc(full_desc),
                'amount': amt,
                'business': business,
                'category': category,
                'split': split,
                'gst_formula': gst,
                'receipt': False,
                'payment': payment_method,
                'account': account_name,
                'notes': notes,
            })
    return txns


def build_row(txn, row_num):
    """Build a sheet row from a transaction dict."""
    gst = txn['gst_formula'].replace('{row}', str(row_num)) if txn['gst_formula'] else ''
    return [
        txn['date_serial'],       # A: Date (serial number)
        txn['vendor'],            # B: Vendor
        txn['description'],       # C: Description
        txn['amount'],            # D: Amount
        txn['business'],          # E: Business (bool)
        txn['category'],          # F: Category
        txn['split'],             # G: Split %
        gst,                      # H: GST
        txn['receipt'],           # I: Receipt (bool)
        txn['payment'],           # J: Payment method
        txn['account'],           # K: Account
        txn['notes'],             # L: Notes
    ]


def run():
    print("=" * 70)
    print("IMPORTING 2026 BANK CSVs")
    print("=" * 70)

    # ── Parse all CSVs ──
    csv_files = [
        ('/Users/matthewfernandes/Downloads/download-transactions (1).csv', 'Chequing', 'Debit'),
        ('/Users/matthewfernandes/Downloads/download-transactions (2).csv', 'Business Chequing', 'Debit'),
        ('/Users/matthewfernandes/Downloads/download-transactions (3).csv', 'Business Card', 'Visa'),
        ('/Users/matthewfernandes/Downloads/download-transactions.csv', 'Personal Card', 'Visa'),
    ]

    all_txns = []
    for filepath, account, payment in csv_files:
        txns = parse_csv(filepath, account, payment)
        print(f"  {account}: {len(txns)} transactions (after filtering)")
        all_txns.extend(txns)

    # ── Separate income vs expenses ──
    income = [t for t in all_txns if t['amount'] > 0 and t['business'] and t['category'] in ('Stripe (Revenue)', 'Business Income')]
    # Everything else that's not income (including personal income like GST/CWB, refunds as expense credits)
    expenses = [t for t in all_txns if t not in income]

    # Move personal "income" (GST, CWB, damage deposits) to expenses section too
    # Actually: positive personal amounts should stay in expenses as credits per the rules
    # Refunds from Amazon/Adobe/MEC with positive amounts stay in EXPENSES section

    # Sort by date
    income.sort(key=lambda t: t['date'])
    expenses.sort(key=lambda t: t['date'])

    print(f"\nTotal: {len(income)} income rows, {len(expenses)} expense rows")

    # ── Build sheet data ──
    svc = get_sheets_service()

    # First, read current sheet to understand structure
    print("\nReading current sheet structure...")
    ss = svc.spreadsheets().get(spreadsheetId=SHEET_ID, fields='sheets.properties').execute()
    sheets = {s['properties']['title']: s['properties']['sheetId'] for s in ss['sheets']}
    TXN = sheets['Transactions']
    print(f"  Transactions sheetId: {TXN}")

    # ── Clear existing transaction data ──
    print("Clearing existing transaction data...")
    # Clear a large range to be safe
    svc.spreadsheets().values().batchClear(
        spreadsheetId=SHEET_ID,
        body={"ranges": [
            "Transactions!A6:N500",   # Income data area
        ]}
    ).execute()

    # ── Calculate row positions ──
    # Row 1: Title
    # Row 2: Subtitle
    # Row 3: Spacer (frozen)
    # Row 4: INCOME header (green bar)
    # Row 5: Column headers
    # Row 6+: Income data
    inc_start = 6  # 1-indexed
    inc_end = inc_start + len(income) - 1

    # 2 spacer rows after income
    spacer1 = inc_end + 1
    spacer2 = inc_end + 2

    # EXPENSES header
    exp_header = inc_end + 3
    exp_cols = inc_end + 4
    exp_start = inc_end + 5
    exp_end = exp_start + len(expenses) - 1

    print(f"  Income rows: {inc_start}-{inc_end} ({len(income)} rows)")
    print(f"  Expenses header: row {exp_header}")
    print(f"  Expense rows: {exp_start}-{exp_end} ({len(expenses)} rows)")

    # ── Build income rows ──
    income_rows = []
    for i, txn in enumerate(income):
        row_num = inc_start + i
        income_rows.append(build_row(txn, row_num))

    # ── Build expense rows ──
    expense_rows = []
    for i, txn in enumerate(expenses):
        row_num = exp_start + i
        expense_rows.append(build_row(txn, row_num))

    # ── Build column headers ──
    col_headers = ['Date', 'Vendor', 'Description', 'Amount', 'Business', 'Category', 'Split %', 'GST', 'Receipt', 'Payment', 'Account', 'Notes']

    # ── Write INCOME section ──
    print("\nWriting data to sheet...")
    write_data = []

    # INCOME header with SUM formula (row 4)
    write_data.append({
        "range": f"Transactions!A4",
        "values": [[f'INCOME                                                    =SUM(D{inc_start}:D{inc_end})']]
    })

    # Income column headers (row 5)
    write_data.append({
        "range": f"Transactions!A5",
        "values": [col_headers]
    })

    # Income data
    if income_rows:
        write_data.append({
            "range": f"Transactions!A{inc_start}:L{inc_end}",
            "values": income_rows
        })

    # EXPENSES header with SUM formula
    write_data.append({
        "range": f"Transactions!A{exp_header}",
        "values": [[f'EXPENSES                                                  =SUM(D{exp_start}:D{exp_end})']]
    })

    # Expense column headers
    write_data.append({
        "range": f"Transactions!A{exp_cols}",
        "values": [col_headers]
    })

    # Expense data
    if expense_rows:
        write_data.append({
            "range": f"Transactions!A{exp_start}:L{exp_end}",
            "values": expense_rows
        })

    # Write all data
    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": write_data}
    ).execute()
    print("  Data written.")

    # ── Add month helper formulas (col N) ──
    print("Adding month helper formulas...")
    month_data = []

    # Income rows
    if income:
        month_formulas_inc = []
        for r in range(inc_start, inc_end + 1):
            month_formulas_inc.append([f'=IF(A{r}="",0,IFERROR(MONTH(A{r}),IFERROR(VALUE(LEFT(A{r},FIND("/",A{r})-1)),0)))'])
        month_data.append({
            "range": f"Transactions!N{inc_start}:N{inc_end}",
            "values": month_formulas_inc
        })

    # Expense rows
    if expenses:
        month_formulas_exp = []
        for r in range(exp_start, exp_end + 1):
            month_formulas_exp.append([f'=IF(A{r}="",0,IFERROR(MONTH(A{r}),IFERROR(VALUE(LEFT(A{r},FIND("/",A{r})-1)),0)))'])
        month_data.append({
            "range": f"Transactions!N{exp_start}:N{exp_end}",
            "values": month_formulas_exp
        })

    if month_data:
        svc.spreadsheets().values().batchUpdate(
            spreadsheetId=SHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": month_data}
        ).execute()
    print("  Month helpers added.")

    # ── FORMATTING ──
    print("\nApplying formatting...")

    # Import format helpers from format_2026_sheet
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
    from format_2026_sheet import (
        gr, rc, mg, um, rh, rhs, cw, tf, border_side, freeze,
        section_bar, col_header, alt_rows, spacer_row, add_footer,
        GREEN, GREEN_BG, RED, RED_BG, BLUE_L, WHITE, ALT_ROW, NAVY, T4, BORDER, GRAY_DIV,
        F_BG, F_TF, F_NF, F_AL, F_VA, F_ALL, F_BG_TF, F_BG_TF_AL,
        ALL_CATS, execute_batch
    )

    NCOLS = 14

    # Clear existing conditional format rules
    ss_full = svc.spreadsheets().get(
        spreadsheetId=SHEET_ID,
        ranges=['Transactions'],
        fields='sheets.conditionalFormats'
    ).execute()
    existing_rules = []
    for sheet in ss_full.get('sheets', []):
        existing_rules = sheet.get('conditionalFormats', [])
        break
    if existing_rules:
        del_reqs = [{"deleteConditionalFormatRule": {"sheetId": TXN, "index": i}}
                    for i in range(len(existing_rules) - 1, -1, -1)]
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID, body={"requests": del_reqs}
        ).execute()
        print(f"  Cleared {len(del_reqs)} conditional rules")

    # 0-indexed row positions
    r_title = 0
    r_subtitle = 1
    r_spacer1 = 2
    r_inc_hdr = 3
    r_inc_cols = 4
    r_inc_start = 5  # row 6
    r_inc_end = r_inc_start + len(income)  # exclusive
    r_spacer2 = r_inc_end
    r_spacer3 = r_inc_end + 1
    r_exp_hdr = r_inc_end + 2
    r_exp_cols = r_inc_end + 3
    r_exp_start = r_inc_end + 4
    r_exp_end = r_exp_start + len(expenses)
    r_footer = r_exp_end + 2

    reqs = []

    # Unmerge existing merges first
    for row in [r_title, r_subtitle, r_inc_hdr, r_exp_hdr]:
        reqs.append(um(TXN, row, row+1, 0, NCOLS))

    # Title
    reqs.append(rh(TXN, r_title, 48))
    reqs.append(rc(TXN, r_title, r_title+1, 0, NCOLS,
        {"backgroundColor": WHITE, "textFormat": tf(bold=True, sz=22, color=NAVY),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(TXN, r_title, r_title+1, 0, NCOLS))

    # Subtitle
    reqs.append(rh(TXN, r_subtitle, 22))
    reqs.append(rc(TXN, r_subtitle, r_subtitle+1, 0, NCOLS,
        {"backgroundColor": WHITE, "textFormat": tf(sz=11, color=T4),
         "verticalAlignment": "MIDDLE"}, F_BG_TF))
    reqs.append(mg(TXN, r_subtitle, r_subtitle+1, 0, NCOLS))

    # Spacer
    reqs.append(rh(TXN, r_spacer1, 12))
    reqs.append(rc(TXN, r_spacer1, r_spacer1+1, 0, NCOLS, {"backgroundColor": WHITE}, F_BG))
    reqs.append(freeze(TXN, rows=3))

    # INCOME header (green bar)
    reqs.append(rh(TXN, r_inc_hdr, 40))
    reqs.append(rc(TXN, r_inc_hdr, r_inc_hdr+1, 0, NCOLS,
        {"backgroundColor": GREEN_BG, "textFormat": tf(bold=True, sz=14, color=GREEN),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(TXN, r_inc_hdr, r_inc_hdr+1, 0, 13))

    # Income column headers
    col_header(reqs, TXN, r_inc_cols, 0, NCOLS, height=30)

    # Income data rows
    if len(income) > 0:
        alt_rows(reqs, TXN, r_inc_start, r_inc_end, 0, NCOLS)
        reqs.append(rhs(TXN, r_inc_start, r_inc_end, 26))
        reqs.append(rc(TXN, r_inc_start, r_inc_end, 0, NCOLS,
            {"textFormat": tf(sz=10)}, F_TF))
        reqs.append(rc(TXN, r_inc_start, r_inc_end, 3, 4,
            {"horizontalAlignment": "RIGHT",
             "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}},
            f"{F_AL},{F_NF}"))
        # Green text for positive amounts
        reqs.append({"addConditionalFormatRule": {"rule": {
            "ranges": [gr(TXN, r_inc_start, r_inc_end, 3, 4)],
            "booleanRule": {"condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                           "format": {"textFormat": {"foregroundColor": GREEN}}}
        }, "index": 0}})

    # Spacer rows
    for r in [r_spacer2, r_spacer3]:
        reqs.append(rh(TXN, r, 12))
        reqs.append(rc(TXN, r, r+1, 0, NCOLS, {"backgroundColor": WHITE}, F_BG))

    # EXPENSES header (red bar)
    reqs.append(rh(TXN, r_exp_hdr, 40))
    reqs.append(rc(TXN, r_exp_hdr, r_exp_hdr+1, 0, NCOLS,
        {"backgroundColor": RED_BG, "textFormat": tf(bold=True, sz=14, color=RED),
         "verticalAlignment": "MIDDLE"}, F_ALL))
    reqs.append(mg(TXN, r_exp_hdr, r_exp_hdr+1, 0, 13))

    # Expense column headers
    col_header(reqs, TXN, r_exp_cols, 0, NCOLS, height=30)

    # Expense data rows
    if len(expenses) > 0:
        alt_rows(reqs, TXN, r_exp_start, r_exp_end, 0, NCOLS)
        reqs.append(rhs(TXN, r_exp_start, r_exp_end, 26))
        reqs.append(rc(TXN, r_exp_start, r_exp_end, 0, NCOLS,
            {"textFormat": tf(sz=10)}, F_TF))
        reqs.append(rc(TXN, r_exp_start, r_exp_end, 3, 4,
            {"horizontalAlignment": "RIGHT",
             "numberFormat": {"type": "CURRENCY", "pattern": "$#,##0.00"}},
            f"{F_AL},{F_NF}"))
        # Red text for negative, green for positive
        reqs.append({"addConditionalFormatRule": {"rule": {
            "ranges": [gr(TXN, r_exp_start, r_exp_end, 3, 4)],
            "booleanRule": {"condition": {"type": "NUMBER_LESS", "values": [{"userEnteredValue": "0"}]},
                           "format": {"textFormat": {"foregroundColor": RED}}}
        }, "index": 0}})
        reqs.append({"addConditionalFormatRule": {"rule": {
            "ranges": [gr(TXN, r_exp_start, r_exp_end, 3, 4)],
            "booleanRule": {"condition": {"type": "NUMBER_GREATER", "values": [{"userEnteredValue": "0"}]},
                           "format": {"textFormat": {"foregroundColor": GREEN}}}
        }, "index": 0}})
        # Blue bg for business rows
        reqs.append({"addConditionalFormatRule": {"rule": {
            "ranges": [gr(TXN, r_exp_start, r_exp_end, 0, NCOLS - 1)],
            "booleanRule": {
                "condition": {"type": "CUSTOM_FORMULA",
                              "values": [{"userEnteredValue": f"=$E{r_exp_start+1}=TRUE"}]},
                "format": {"backgroundColor": BLUE_L}
            }
        }, "index": 0}})

    # Date format for all data rows
    for sr, er in [(r_inc_start, r_inc_end), (r_exp_start, r_exp_end)]:
        reqs.append(rc(TXN, sr, er, 0, 1,
            {"numberFormat": {"type": "DATE", "pattern": "MMM d, yyyy"}}, F_NF))

    # Column widths
    col_widths = [105, 180, 200, 110, 80, 200, 60, 90, 80, 90, 120, 140, 20]
    for c, w in enumerate(col_widths):
        reqs.append(cw(TXN, c, w))

    # Hide col N
    reqs.append({"updateDimensionProperties": {
        "range": {"sheetId": TXN, "dimension": "COLUMNS", "startIndex": 13, "endIndex": 14},
        "properties": {"hiddenByUser": True}, "fields": "hiddenByUser"
    }})

    # Footer
    add_footer(reqs, TXN, r_footer, 0, 13)

    # Global Inter font
    reqs.append(rc(TXN, 0, r_footer + 5, 0, NCOLS,
        {"textFormat": {"fontFamily": "Inter"}},
        "userEnteredFormat.textFormat.fontFamily"))

    execute_batch(svc, reqs, "Transactions formatting")

    # ── Write text values ──
    print("Writing section headers and footer text...")
    val_data = [
        {"range": "Transactions!A1", "values": [["Transactions · 2026"]]},
        {"range": "Transactions!A2", "values": [["All income and expenses  ·  Tax Year 2026"]]},
        {"range": f"Transactions!A{r_footer+3}", "values": [["Prepared by: Matt Anthony Photography"]]},
        {"range": f"Transactions!A{r_footer+4}", "values": [["Tax Year: 2026  |  Filing: June 15, 2028  |  GST: Quarterly"]]},
        {"range": f"Transactions!A{r_footer+5}", "values": [["This document supports T2125 Statement of Business Activities"]]},
    ]
    svc.spreadsheets().values().batchUpdate(
        spreadsheetId=SHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": val_data}
    ).execute()

    # ── Checkboxes and dropdowns ──
    print("Applying checkboxes and category dropdowns...")
    checkbox_reqs = []
    for sr, er in [(r_inc_start, r_inc_end), (r_exp_start, r_exp_end)]:
        if er > sr:
            # Business col E
            checkbox_reqs.append({"setDataValidation": {
                "range": gr(TXN, sr, er, 4, 5),
                "rule": {"condition": {"type": "BOOLEAN"}, "strict": True, "showCustomUi": True}
            }})
            # Receipt col I
            checkbox_reqs.append({"setDataValidation": {
                "range": gr(TXN, sr, er, 8, 9),
                "rule": {"condition": {"type": "BOOLEAN"}, "strict": True, "showCustomUi": True}
            }})
            # Category dropdown col F
            checkbox_reqs.append({"setDataValidation": {
                "range": gr(TXN, sr, er, 5, 6),
                "rule": {
                    "condition": {"type": "ONE_OF_LIST",
                                  "values": [{"userEnteredValue": c} for c in ALL_CATS]},
                    "strict": False, "showCustomUi": True
                }
            }})

    if checkbox_reqs:
        svc.spreadsheets().batchUpdate(
            spreadsheetId=SHEET_ID, body={"requests": checkbox_reqs}
        ).execute()
    print("  Checkboxes and dropdowns applied.")

    # ── SUMMARY STATS ──
    print("\n" + "=" * 70)
    print("IMPORT COMPLETE")
    print("=" * 70)

    # Transactions by account
    from collections import Counter, defaultdict
    account_counts = Counter(t['account'] for t in all_txns)
    print("\nTransactions by account:")
    for acc, cnt in sorted(account_counts.items()):
        print(f"  {acc}: {cnt}")

    print(f"\nIncome: {len(income)} transactions, total ${sum(t['amount'] for t in income):,.2f}")
    print(f"Expenses: {len(expenses)} transactions, total ${sum(t['amount'] for t in expenses):,.2f}")

    biz_expenses = [t for t in expenses if t['business'] and t['amount'] < 0]
    personal_expenses = [t for t in expenses if not t['business'] and t['amount'] < 0]

    biz_total = sum(t['amount'] for t in biz_expenses)
    personal_total = sum(t['amount'] for t in personal_expenses)

    print(f"\nBusiness expense total: ${biz_total:,.2f}")
    print(f"Personal expense total: ${personal_total:,.2f}")

    # Top 10 business categories
    cat_totals = defaultdict(float)
    for t in biz_expenses:
        cat_totals[t['category']] += abs(t['amount'])

    print("\nTop 10 business expense categories:")
    for cat, total in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {cat}: ${total:,.2f}")

    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    print(f"\nSheet: {url}")
    return url


if __name__ == '__main__':
    run()
