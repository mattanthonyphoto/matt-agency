"""Shared utilities for local agent scripts — Telegram, GHL, Instantly, Google APIs."""
import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

# === TELEGRAM ===
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8186928770:AAHdsaUe761y7W-1j-0VQoIxfBVCpla19_8")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8780007312")

def send_telegram(text):
    """Send HTML message to Telegram. Auto-splits if >4096 chars."""
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    chunks = []
    while len(text) > 4096:
        split = text[:4096].rfind('\n')
        if split == -1:
            split = 4096
        chunks.append(text[:split])
        text = text[split:]
    chunks.append(text)
    for chunk in chunks:
        r = requests.post(url, json={"chat_id": TG_CHAT_ID, "text": chunk, "parse_mode": "HTML"})
        if not r.ok:
            print(f"Telegram error: {r.status_code} {r.text}")

# === GHL ===
GHL_KEY = os.getenv("GHL_API_KEY")
GHL_LOC = os.getenv("GHL_LOCATION_ID")
GHL_BASE = "https://services.leadconnectorhq.com"
GHL_HEADERS = {"Authorization": f"Bearer {GHL_KEY}", "Version": "2021-07-28"}

def ghl_get(endpoint, params=None):
    r = requests.get(f"{GHL_BASE}{endpoint}", headers=GHL_HEADERS, params=params)
    return r.json() if r.ok else {}

def get_ghl_contacts(limit=100):
    return ghl_get("/contacts/", {"locationId": GHL_LOC, "limit": limit})

def get_ghl_opportunities(limit=100):
    return ghl_get("/opportunities/search", {"location_id": GHL_LOC, "limit": limit})

def get_ghl_invoices():
    return ghl_get("/invoices/", {"altType": "location", "altId": GHL_LOC, "limit": 100, "offset": 0, "status": "all"})

# === INSTANTLY ===
INSTANTLY_KEY = os.getenv("INSTANTLY_API_KEY")
INSTANTLY_HEADERS = {"Authorization": f"Bearer {INSTANTLY_KEY}"}

def instantly_get(endpoint, params=None):
    r = requests.get(f"https://api.instantly.ai/api/v2{endpoint}", headers=INSTANTLY_HEADERS, params=params)
    return r.json() if r.ok else {}

def get_instantly_campaigns():
    return instantly_get("/campaigns")

def get_instantly_replies():
    return instantly_get("/unibox/emails", {"email_type": "received", "limit": 50})

# === GOOGLE (Gmail + Calendar) ===
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
TOKEN_PATH = os.path.join(os.path.dirname(__file__), "..", "token.json")
CREDS_PATH = os.path.join(os.path.dirname(__file__), "..", "credentials.json")

def get_google_creds():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, "w") as f:
                f.write(creds.to_json())
    return creds

def get_gmail_service():
    return build("gmail", "v1", credentials=get_google_creds())

def get_calendar_service():
    """Get Calendar via API key-free approach using service discovery."""
    # Calendar needs its own OAuth scope which requires re-auth.
    # Use a direct REST call with the existing token instead.
    creds = get_google_creds()
    return creds  # Return creds for manual REST calls

def search_gmail(query, max_results=20):
    """Search Gmail, return list of message summaries."""
    svc = get_gmail_service()
    results = svc.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    messages = []
    for msg in results.get("messages", []):
        detail = svc.users().messages().get(userId="me", id=msg["id"], format="metadata",
                                             metadataHeaders=["From", "To", "Subject", "Date"]).execute()
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        messages.append({
            "id": msg["id"],
            "threadId": detail.get("threadId"),
            "snippet": detail.get("snippet", ""),
            "from": headers.get("From", ""),
            "to": headers.get("To", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "labels": detail.get("labelIds", []),
        })
    return messages

def _calendar_api_call(time_min, time_max):
    """Hit Google Calendar REST API directly using OAuth token."""
    creds = get_google_creds()
    headers = {"Authorization": f"Bearer {creds.token}"}
    params = {
        "timeMin": time_min,
        "timeMax": time_max,
        "singleEvents": "true",
        "orderBy": "startTime",
        "timeZone": "America/Vancouver",
    }
    r = requests.get("https://www.googleapis.com/calendar/v3/calendars/primary/events",
                     headers=headers, params=params)
    if r.ok:
        return r.json().get("items", [])
    print(f"Calendar API error: {r.status_code} — {r.text[:200]}")
    return []

def get_today_events():
    """Get today's calendar events in Vancouver time."""
    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0).isoformat() + "-07:00"
    end = now.replace(hour=23, minute=59, second=59).isoformat() + "-07:00"
    return _calendar_api_call(start, end)

def get_week_events():
    """Get next 7 days of calendar events."""
    now = datetime.now()
    start = now.replace(hour=0, minute=0, second=0).isoformat() + "-07:00"
    end = (now + timedelta(days=7)).replace(hour=23, minute=59, second=59).isoformat() + "-07:00"
    return _calendar_api_call(start, end)
