"""
Import bank CSV transactions into the v2 interactive finance sheet.
Maps to the Transactions tab with checkboxes and category dropdowns.
"""
import csv
import os
import sys
import re
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.google_sheets_auth import get_sheets_service

SHEET_ID = "1QvUEuDVyaofCBskes69pZPDu76D0Xh3_swJISdDmU98"

# ── Categorization rules ──
# (pattern, is_business, category, clean_name, split%)
RULES = [
    # 100% Business — Software & Subscriptions
    (r"GOOGLE\*WORKSPACE|GOOGLE \*Workspace", True, "Software & Subscriptions", "Google Workspace", 100),
    (r"Adobe Inc", True, "Software & Subscriptions", "Adobe Creative Cloud", 100),
    (r"INSTANTLY", True, "Software & Subscriptions", "Instantly (Cold Email)", 100),
    (r"BUFFER PLAN", True, "Software & Subscriptions", "Buffer (Social Media)", 100),
    (r"OPENROUTER", True, "Software & Subscriptions", "OpenRouter (AI)", 100),
    (r"LEADGENJAY", True, "Software & Subscriptions", "LeadGenJay", 100),
    (r"APIFY", True, "Software & Subscriptions", "Apify (Scraping)", 100),
    (r"CLICKUP", True, "Software & Subscriptions", "ClickUp", 100),
    (r"EpidemicSound", True, "Software & Subscriptions", "Epidemic Sound", 100),
    (r"Dropbox", True, "Software & Subscriptions", "Dropbox", 100),
    (r"INTUIT.*QBooks", True, "Software & Subscriptions", "QuickBooks", 100),
    (r"HIGHLEVEL", True, "Software & Subscriptions", "GoHighLevel (CRM)", 100),
    (r"ICYPEAS", True, "Software & Subscriptions", "IcyPeas (Email Verify)", 100),
    (r"OPENAI.*CHATGPT", True, "Software & Subscriptions", "ChatGPT Plus", 100),
    (r"Audible", True, "Software & Subscriptions", "Audible (Prof Dev)", 100),
    (r"EXPRESSVPN", True, "Software & Subscriptions", "ExpressVPN", 100),
    # Business — Advertising
    (r"SHOWPASS", True, "Advertising & Marketing", "Event / Networking", 100),
    # Business — Rent
    (r"OUTPOST LANKA", True, "Rent / Co-working", "Outpost Lanka", 100),
    # 50% Business — Travel
    (r"AIRALO", True, "Travel", "Airalo eSIM", 50),
    (r"ONWARD TICKET", True, "Travel", "Onward Ticket", 50),
    (r"CATHAYPACAIR", True, "Travel", "Cathay Pacific Flight", 50),
    (r"AIR ASIA", True, "Travel", "AirAsia Flight", 50),
    (r"DEPARTMENT OF IMMIGRATION|DEPT OF IMMIGRATION", True, "Travel", "Visa Fee", 50),
    (r"A4 RESIDENCE COLOMBO", True, "Travel", "Accommodation (Sri Lanka)", 50),
    (r"Clear Point Wild Forest", True, "Travel", "Accommodation (Sri Lanka)", 50),
    (r"XDT\*MEGATIX", True, "Travel", "Event (Bali)", 50),
    # 50% Business — Telephone
    (r"AIRALO", True, "Telephone & Internet", "Airalo eSIM", 50),
    # Personal — Dining
    (r"BACKCOUNTRY BREWING", False, "Dining Out", "Backcountry Brewing", 0),
    (r"IL MUNDO", False, "Dining Out", "Il Mundo", 0),
    (r"PUREBREAD", False, "Dining Out", "Purebread Bakery", 0),
    (r"DOMINOS", False, "Dining Out", "Domino's Pizza", 0),
    (r"RAMEN BUTCHER", False, "Dining Out", "Ramen Butcher", 0),
    (r"Buddha 2", False, "Dining Out", "Buddha 2", 0),
    (r"CRABAPPLE CAFE", False, "Dining Out", "Crabapple Cafe", 0),
    (r"STARBUCKS", False, "Dining Out", "Starbucks", 0),
    (r"SUBWAY", False, "Dining Out", "Subway", 0),
    (r"BARBURRITO", False, "Dining Out", "Barburrito", 0),
    (r"BAKED BATU", False, "Dining Out", "Baked (Bali)", 0),
    (r"ZIN CAFE", False, "Dining Out", "Zin Cafe (Bali)", 0),
    (r"GAYA GELATO", False, "Dining Out", "Gaya Gelato (Bali)", 0),
    (r"SOOGI ROLL", False, "Dining Out", "Soogi Roll (Bali)", 0),
    (r"AVOCADO FACTORY", False, "Dining Out", "Avocado Factory (Bali)", 0),
    (r"GOAT FATHER", False, "Dining Out", "Goat Father (Bali)", 0),
    (r"MOTION PERERENAN", False, "Dining Out", "Motion (Bali)", 0),
    (r"KAYUNAN WARUNG", False, "Dining Out", "Kayunan Warung (Bali)", 0),
    (r"RUSTERS", False, "Dining Out", "Rusters (Bali)", 0),
    (r"CLEAR CAFE", False, "Dining Out", "Clear Cafe (Bali)", 0),
    (r"GIGI SUSU", False, "Dining Out", "Gigi Susu (Bali)", 0),
    (r"REVOLVER INTER", False, "Dining Out", "Revolver (Bali)", 0),
    (r"ALCHEMY CANGGU", False, "Dining Out", "Alchemy Canggu (Bali)", 0),
    (r"AHH-YUM", False, "Dining Out", "Ahh-Yum (Malaysia)", 0),
    (r"PLAN B CAFE", False, "Dining Out", "Plan B Cafe (Sri Lanka)", 0),
    (r"STICK SURF CLUB", False, "Dining Out", "Stick Surf Club (Sri Lanka)", 0),
    (r"LAMANA", False, "Dining Out", "Lamana (Sri Lanka)", 0),
    (r"JAVA LOUNGE", False, "Dining Out", "Java Lounge (Sri Lanka)", 0),
    (r"AHANGAMA DAIRIES", False, "Dining Out", "Ahangama Dairies", 0),
    (r"ZIPPI PVT", False, "Dining Out", "Zippi (Sri Lanka)", 0),
    (r"TUGU BALI", False, "Dining Out", "Tugu Bali", 0),
    (r"H A C PERERA", False, "Dining Out", "H A C Perera (Sri Lanka)", 0),
    (r"DEVILLE COFFEE", False, "Dining Out", "Deville Coffee", 0),
    (r"COMPASS VENDING", False, "Dining Out", "Compass Vending", 0),
    (r"MOON THAI EXPRESS", False, "Dining Out", "Moon Thai (HK Airport)", 0),
    (r"2410311_HKG.*Gordon", False, "Dining Out", "Gordon Ramsay (HK)", 0),
    (r"CHAI RESTAURANTS", False, "Dining Out", "Chai Restaurant", 0),
    (r"TRAFIQ CAFE", False, "Dining Out", "Trafiq Cafe", 0),
    (r"CONTINENTAL COFFEE", False, "Dining Out", "Continental Coffee", 0),
    (r"SUSHI SEN", False, "Dining Out", "Sushi Sen", 0),
    (r"Noodlebox", False, "Dining Out", "Noodlebox", 0),
    (r"ESSENCE OF INDIA", False, "Dining Out", "Essence of India", 0),
    (r"SEA TO SKY HOTEL", False, "Dining Out", "Sea to Sky Hotel", 0),
    (r"Brackendale Art Ga", False, "Dining Out", "Brackendale Art Gallery", 0),
    (r"FOX & OAK", False, "Dining Out", "Fox & Oak", 0),
    (r"CLOUDBURST CAFE", False, "Dining Out", "Cloudburst Cafe", 0),
    (r"SHEN HENG CHANG", False, "Dining Out", "Food (Taiwan)", 0),
    (r"WHSMITH", False, "Dining Out", "WHSmith (Bali)", 0),
    # Groceries
    (r"HOME DEPOT", False, "Groceries", "Home Depot", 0),
    (r"HECTOR.S YOUR INDEPEND", False, "Groceries", "Hector's IGA", 0),
    (r"DOLLARAMA", False, "Groceries", "Dollarama", 0),
    (r"LONDON DRUGS", False, "Groceries", "London Drugs", 0),
    (r"SWAN MART", False, "Groceries", "Swan Mart (Bali)", 0),
    (r"NESTERS MARKET", False, "Groceries", "Nesters Market", 0),
    (r"CHV.*WESTMOUNT", False, "Groceries", "Cheese Shop", 0),
    # Clothing
    (r"MARKS SQUAMISH", False, "Clothing", "Mark's", 0),
    (r"MOUNTAIN EQUIPMENT", False, "Clothing", "MEC", 0),
    (r"COASTAL CRYSTALS", False, "Clothing", "Coastal Crystals", 0),
    # Subscriptions (Personal)
    (r"Spotify", False, "Subscriptions", "Spotify", 0),
    (r"APPLE\.COM/BILL", False, "Subscriptions", "Apple Services", 0),
    # Health
    (r"CLIMB GROUNDUP", False, "Health & Fitness", "Ground Up Climbing", 0),
    (r"BAMBU FITNESS", False, "Health & Fitness", "Bambu Fitness (Bali)", 0),
    (r"MISSION YOGA", False, "Health & Fitness", "Mission Yoga (Bali)", 0),
    (r"ALCHEMY YOGA", False, "Health & Fitness", "Alchemy Yoga (Bali)", 0),
    (r"SENSES YOGA", False, "Health & Fitness", "Senses Yoga (Sri Lanka)", 0),
    # Transportation
    (r"UBER", False, "Transportation", "Uber", 0),
    (r"CITY OF VANCOUVER PARKING", False, "Transportation", "Parking", 0),
    (r"AIR-SERV", False, "Transportation", "Gas Station", 0),
    (r"SQUAMISHCONNECTOR", False, "Transportation", "Squamish Connector", 0),
]


def categorize(desc):
    for pattern, is_biz, category, name, split in RULES:
        if re.search(pattern, desc, re.IGNORECASE):
            return is_biz, category, name, split
    return False, "Other Personal", desc.split("  ")[0].strip()[:30], 0


def calc_gst(amount):
    return round(abs(amount) / 1.05 * 0.05, 2)


def main():
    csv_path = "/Users/matthewfernandes/Downloads/download-transactions.csv"
    sheets = get_sheets_service()

    rows = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            amt_str = row.get("CAD$", "").strip()
            if not amt_str:
                continue
            amount = float(amt_str)
            desc = f"{row.get('Description 1', '')} {row.get('Description 2', '')}".strip()
            date = row.get("Transaction Date", "").strip()
            acct_num = row.get("Account Number", "")[-4:]

            # Skip card payments
            if amount > 0 and "PAYMENT" in desc.upper():
                continue

            is_biz, category, name, split_pct = categorize(desc)
            gst = calc_gst(amount) if is_biz and amount < 0 else 0

            # For 50% splits, create TWO rows
            if split_pct == 50 and amount < 0:
                biz_amt = round(amount / 2, 2)
                pers_amt = round(amount / 2, 2)
                biz_gst = calc_gst(biz_amt)

                # Business half
                rows.append([
                    date, name, f"50% business — {desc.split('  ')[0][:30]}",
                    biz_amt, True, category, "50%", biz_gst,
                    False, "Visa", "Personal Card", "50/50 split"
                ])
                # Personal half
                pers_cat = "Travel (Personal)" if category == "Travel" else "Entertainment"
                rows.append([
                    date, name, f"50% personal — {desc.split('  ')[0][:30]}",
                    pers_amt, False, pers_cat, "0%", 0,
                    False, "Visa", "Personal Card", "50/50 split"
                ])
            else:
                # Refunds are positive, expenses negative
                rows.append([
                    date, name, desc.split("  ")[0][:40],
                    amount, is_biz, category,
                    "100%" if is_biz else "0%",
                    gst, False, "Visa", "Personal Card", ""
                ])

    # Sort by date
    rows.sort(key=lambda x: datetime.strptime(x[0], "%m/%d/%Y"))

    print(f"Total rows: {len(rows)}")
    biz_count = sum(1 for r in rows if r[4] is True)
    pers_count = sum(1 for r in rows if r[4] is False)
    print(f"Business: {biz_count}, Personal: {pers_count}")

    # Write to Transactions tab starting at row 6 (row 5 is header in v3)
    # v3 has spacer col A, so shift all data right by 1
    shifted_rows = [[""] + r for r in rows]
    start_row = 6
    end_row = start_row + len(shifted_rows) - 1

    sheets.spreadsheets().values().update(
        spreadsheetId=SHEET_ID,
        range=f"'⬡  Transactions'!A{start_row}:M{end_row}",
        valueInputOption="USER_ENTERED",
        body={"values": shifted_rows}
    ).execute()

    print(f"Written to rows {start_row}–{end_row}")

    # Business total
    biz_total = sum(abs(r[3]) for r in rows if r[4] is True and r[3] < 0)
    pers_total = sum(abs(r[3]) for r in rows if r[4] is False and r[3] < 0)
    gst_total = sum(r[7] for r in rows if r[4] is True and r[7] > 0)

    print(f"\nBusiness expenses: ${biz_total:,.2f}")
    print(f"Personal expenses: ${pers_total:,.2f}")
    print(f"GST ITCs: ${gst_total:,.2f}")
    print("\nDone! Check the sheet — toggle Business checkboxes to reclassify anything.")


if __name__ == "__main__":
    main()
