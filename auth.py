import os
from typing import Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

# Scopes needed: Read-only access to Drive, and Send permission for Gmail
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(BASE_DIR, "credentials.json")
TOKEN_FILE = os.path.join(BASE_DIR, "token.json")

def get_credentials_path() -> Optional[str]:
    if os.path.exists(CREDENTIALS_FILE):
        return CREDENTIALS_FILE
    # Also look for any downloaded client_secret_*.json
    secrets = glob.glob(os.path.join(BASE_DIR, "client_secret_*.json"))
    if secrets:
        return secrets[0]
    return None

def check_credentials_exist() -> bool:
    return get_credentials_path() is not None

def get_credentials() -> Optional[Credentials]:
    """
    Authenticates the user with Google OAuth 2.0.
    Returns Credentials or raises an Exception if credentials.json is missing.
    """
    creds = None
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception:
            creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                creds = None

        if not creds:
            cred_path = get_credentials_path()
            if not cred_path:
                raise FileNotFoundError(
                    f"Missing 'credentials.json'.\n"
                    "Please download your OAuth client ID credentials from Google Cloud Console "
                    "and save the file as 'credentials.json' in this folder."
                )

            flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the credentials for the next run
        with open(TOKEN_FILE, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())

    return creds

def get_services() -> Tuple[Resource, Resource]:
    """
    Returns (drive_service, gmail_service) tuple.
    """
    creds = get_credentials()
    drive_service = build('drive', 'v3', credentials=creds)
    gmail_service = build('gmail', 'v1', credentials=creds)
    return drive_service, gmail_service
