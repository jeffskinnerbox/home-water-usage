"""Tests for auth.py: credentials discovery, OAuth flow, token write + chmod 600."""
import dataclasses
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import home_water_usage.auth as auth_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_creds(valid=True):
    creds = MagicMock()
    creds.valid = valid
    creds.expired = not valid
    creds.refresh_token = "refresh-token" if not valid else None
    creds.to_json.return_value = '{"token": "dummy", "refresh_token": "r"}'
    return creds


# ---------------------------------------------------------------------------
# 3-step credentials discovery
# ---------------------------------------------------------------------------

@patch("home_water_usage.auth.build")
@patch("home_water_usage.auth.InstalledAppFlow")
@patch("home_water_usage.auth.Credentials")
def test_step1_default_path(mock_Creds, mock_Flow, mock_build, base_config, tmp_path):
    """Step 1: credentials.json found at the hardcoded default path."""
    default_creds = tmp_path / "default_creds.json"
    default_creds.write_text('{"installed": {}}')

    mock_Creds.from_authorized_user_file.side_effect = FileNotFoundError
    mock_creds = _make_mock_creds()
    mock_Flow.from_client_secrets_file.return_value.run_local_server.return_value = mock_creds

    with patch.object(auth_module, "_DEFAULT_CREDS_PATH", default_creds):
        auth_module.get_service(base_config)

    mock_Flow.from_client_secrets_file.assert_called_once_with(str(default_creds), auth_module._SCOPES)


@patch("home_water_usage.auth.build")
@patch("home_water_usage.auth.InstalledAppFlow")
@patch("home_water_usage.auth.Credentials")
def test_step2_env_var(mock_Creds, mock_Flow, mock_build, base_config, tmp_path, monkeypatch):
    """Step 2: default path missing; GMAIL_CREDENTIALS_PATH env var used."""
    env_creds = tmp_path / "env_creds.json"
    env_creds.write_text('{"installed": {}}')

    monkeypatch.setenv("GMAIL_CREDENTIALS_PATH", str(env_creds))
    mock_Creds.from_authorized_user_file.side_effect = FileNotFoundError
    mock_creds = _make_mock_creds()
    mock_Flow.from_client_secrets_file.return_value.run_local_server.return_value = mock_creds

    missing = tmp_path / "nonexistent.json"
    with patch.object(auth_module, "_DEFAULT_CREDS_PATH", missing):
        auth_module.get_service(base_config)

    mock_Flow.from_client_secrets_file.assert_called_once_with(str(env_creds), auth_module._SCOPES)


@patch("home_water_usage.auth.build")
@patch("home_water_usage.auth.InstalledAppFlow")
@patch("home_water_usage.auth.Credentials")
def test_step3_cli_flag(mock_Creds, mock_Flow, mock_build, base_config, tmp_path, monkeypatch):
    """Step 3: default + env var missing; config.credentials_path used."""
    cli_creds = tmp_path / "cli_creds.json"
    cli_creds.write_text('{"installed": {}}')
    config = dataclasses.replace(base_config, credentials_path=str(cli_creds))

    monkeypatch.delenv("GMAIL_CREDENTIALS_PATH", raising=False)
    mock_Creds.from_authorized_user_file.side_effect = FileNotFoundError
    mock_creds = _make_mock_creds()
    mock_Flow.from_client_secrets_file.return_value.run_local_server.return_value = mock_creds

    missing = tmp_path / "nonexistent.json"
    with patch.object(auth_module, "_DEFAULT_CREDS_PATH", missing):
        auth_module.get_service(config)

    mock_Flow.from_client_secrets_file.assert_called_once_with(str(cli_creds), auth_module._SCOPES)


def test_missing_credentials_aborts(base_config, tmp_path, monkeypatch):
    """All 3 locations missing → [✗] message with numbered paths + exit(1)."""
    monkeypatch.delenv("GMAIL_CREDENTIALS_PATH", raising=False)
    config = dataclasses.replace(base_config, credentials_path=str(tmp_path / "nope.json"))
    missing = tmp_path / "nonexistent.json"

    with patch.object(auth_module, "_DEFAULT_CREDS_PATH", missing):
        with patch("home_water_usage.auth.status") as mock_status:
            mock_status.error.side_effect = SystemExit(1)
            with pytest.raises(SystemExit) as exc:
                auth_module.get_service(config)

    assert exc.value.code == 1
    call_args = mock_status.error.call_args
    msg = call_args[0][0]
    likely_cause = call_args[1].get("likely_cause", "")
    remediation = call_args[1].get("remediation", "")
    assert "not found" in msg
    assert "1." in likely_cause and "2." in likely_cause and "3." in likely_cause
    assert remediation


# ---------------------------------------------------------------------------
# Token write + chmod 600
# ---------------------------------------------------------------------------

@patch("home_water_usage.auth.build")
@patch("home_water_usage.auth.InstalledAppFlow")
@patch("home_water_usage.auth.Credentials")
def test_token_written_and_chmod_600(mock_Creds, mock_Flow, mock_build, base_config, tmp_path):
    """token.json written and chmod 600 applied."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text('{"installed": {}}')
    token_path = tmp_path / "token.json"
    config = dataclasses.replace(
        base_config,
        credentials_path=str(creds_file),
        token_path=str(token_path),
    )

    mock_Creds.from_authorized_user_file.side_effect = FileNotFoundError
    mock_creds = _make_mock_creds()
    mock_Flow.from_client_secrets_file.return_value.run_local_server.return_value = mock_creds

    with patch.object(auth_module, "_DEFAULT_CREDS_PATH", tmp_path / "no_default.json"):
        auth_module.get_service(config)

    assert token_path.exists()
    mode = os.stat(str(token_path)).st_mode & 0o777
    assert mode == 0o600


# ---------------------------------------------------------------------------
# Token refresh when expired
# ---------------------------------------------------------------------------

@patch("home_water_usage.auth.build")
@patch("home_water_usage.auth.Request")
@patch("home_water_usage.auth.Credentials")
def test_expired_token_refreshed(mock_Creds, mock_Request, mock_build, base_config, tmp_path):
    """Expired token with refresh_token → refresh() called instead of new flow."""
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text('{"installed": {}}')
    token_path = tmp_path / "token.json"
    token_path.write_text('{"token": "old"}')
    config = dataclasses.replace(
        base_config,
        credentials_path=str(creds_file),
        token_path=str(token_path),
    )

    stale = MagicMock()
    stale.valid = False
    stale.expired = True
    stale.refresh_token = "a-refresh-token"
    stale.to_json.return_value = '{"token": "refreshed"}'
    mock_Creds.from_authorized_user_file.return_value = stale

    with patch.object(auth_module, "_DEFAULT_CREDS_PATH", tmp_path / "no_default.json"):
        auth_module.get_service(config)

    stale.refresh.assert_called_once()
