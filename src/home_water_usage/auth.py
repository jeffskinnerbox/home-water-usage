"""Gmail OAuth 2.0: 3-step credentials discovery, token cache, service build."""
from __future__ import annotations

import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from home_water_usage import status

_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
_DEFAULT_CREDS_PATH = Path.home() / ".config/home-water-usage/credentials.json"
_ENV_VAR = "GMAIL_CREDENTIALS_PATH"


def _discover_credentials_path(config) -> Path:
    """Try 3 locations for credentials.json; return first found or exit 1."""
    # Step 1: hardcoded default
    if _DEFAULT_CREDS_PATH.exists():
        return _DEFAULT_CREDS_PATH

    # Step 2: GMAIL_CREDENTIALS_PATH env var
    env_val = os.environ.get(_ENV_VAR)
    if env_val:
        p = Path(env_val)
        if p.exists():
            return p

    # Step 3: config.credentials_path (from --credentials-path CLI flag)
    cli_path = Path(config.credentials_path).expanduser()
    if cli_path.exists():
        return cli_path

    env_val = os.environ.get(_ENV_VAR)
    env_note = env_val if env_val else "(not set)"
    status.error(
        "credentials.json not found at any discovery location.",
        likely_cause=(
            f"Tried:\n"
            f"  1. {_DEFAULT_CREDS_PATH}\n"
            f"  2. ${_ENV_VAR} = {env_note}\n"
            f"  3. --credentials-path {cli_path}"
        ),
        remediation=(
            "Download credentials.json from Google Cloud Console "
            "and place it at ~/.config/home-water-usage/credentials.json"
        ),
    )


def _authenticate(creds_path: Path, config) -> Credentials:
    """Load cached token or run OAuth flow; refresh if expired."""
    token_path = Path(config.token_path).expanduser()
    creds = None

    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), _SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), _SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
        os.chmod(str(token_path), 0o600)

    return creds


def get_service(config):
    """Discover credentials, authenticate, return Gmail API service."""
    creds_path = _discover_credentials_path(config)
    creds = _authenticate(creds_path, config)
    return build("gmail", "v1", credentials=creds)
