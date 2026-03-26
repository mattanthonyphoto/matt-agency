"""Google Sheets authentication helper.
Handles OAuth flow and provides authenticated service objects.
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def get_credentials():
    """Get valid credentials, refreshing or running OAuth flow as needed."""
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def get_sheets_service():
    """Return an authenticated Google Sheets API service."""
    creds = get_credentials()
    return build("sheets", "v4", credentials=creds)


def get_drive_service():
    """Return an authenticated Google Drive API service."""
    creds = get_credentials()
    return build("drive", "v3", credentials=creds)


if __name__ == "__main__":
    # Test authentication
    creds = get_credentials()
    print("Authentication successful!")
    print(f"Token saved to {TOKEN_FILE}")
