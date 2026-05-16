#!/usr/bin/env python3
"""
Run once locally to authorize Tony's Google Drive access.
Prints the env vars to paste into Render.

Usage:
  1. Download OAuth2 Desktop credentials from GCP Console as client_secrets.json
     (APIs & Services → Credentials → Create OAuth Client ID → Desktop app → Download JSON)
  2. python3 scripts/authorize_drive.py
  3. Browser opens → sign in as tony.cerafield@gmail.com → Allow
  4. Copy the 3 env vars printed below into Render
"""
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Run: pip install google-auth-oauthlib")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]
SECRETS_FILE = Path(__file__).parent / "client_secrets.json"

if not SECRETS_FILE.exists():
    print(f"Missing: {SECRETS_FILE}")
    print("Download OAuth2 Desktop credentials from GCP Console and save as scripts/client_secrets.json")
    sys.exit(1)

flow = InstalledAppFlow.from_client_secrets_file(str(SECRETS_FILE), SCOPES)
creds = flow.run_local_server(port=0)

print("\n=== Add these 3 env vars to Render ===\n")
print(f"GOOGLE_OAUTH_CLIENT_ID={creds.client_id}")
print(f"GOOGLE_OAUTH_CLIENT_SECRET={creds.client_secret}")
print(f"GOOGLE_OAUTH_REFRESH_TOKEN={creds.refresh_token}")
print("\n=====================================")
