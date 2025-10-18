"""Tests for authentication and authorization functionality."""
import pytest
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import get_current_user, validate_api_key


def setup_request_mock(mocker, is_local=False):
    """Helper to create request mock"""
    request = mocker.Mock(spec=Request)
    request.client = mocker.Mock()
    request.client.host = "127.0.0.1" if is_local else "8.8.8.8"
    return request


def test_debug_mode_no_credentials(mocker):
    """Test debug mode returns dummy user when no credentials provided"""
    mock_settings = mocker.Mock()
    mock_settings.debug_mode = True
    mocker.patch('app.core.auth.get_settings', return_value=mock_settings)

    request = setup_request_mock(mocker, is_local=True)
    result = get_current_user(request, credentials=None)

    assert result["uid"] == "debug-uid"
    assert result["role"] == "authenticated"
    assert result["is_debug"] is True


def test_production_mode_no_credentials(mocker):
    """Test production mode raises 403 without credentials"""
    mock_settings = mocker.Mock()
    mock_settings.debug_mode = False
    mocker.patch('app.core.auth.get_settings', return_value=mock_settings)

    request = setup_request_mock(mocker)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request, credentials=None)

    assert exc_info.value.status_code == 403


def test_production_mode_valid_token(mocker):
    """Test production mode with valid token"""
    mock_settings = mocker.Mock()
    mock_settings.debug_mode = False
    mocker.patch('app.core.auth.get_settings', return_value=mock_settings)

    mock_user = {"uid": "test123", "role": "authenticated"}
    mocker.patch('app.core.auth.verify_firebase_token', return_value=mock_user)

    request = setup_request_mock(mocker)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    result = get_current_user(request, credentials)

    assert result["uid"] == "test123"
    assert result["role"] == "authenticated"


def test_production_mode_invalid_role(mocker):
    """Test production mode rejects invalid roles"""
    mock_settings = mocker.Mock()
    mock_settings.debug_mode = False
    mocker.patch('app.core.auth.get_settings', return_value=mock_settings)

    mock_user = {"uid": "test123", "role": "invalid_role"}
    mocker.patch('app.core.auth.verify_firebase_token', return_value=mock_user)

    request = setup_request_mock(mocker)
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(request, credentials)

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_api_key_validation(mocker):
    """Test API key validation"""
    mock_settings = mocker.Mock()
    mock_settings.api_key = "valid-key"
    mocker.patch('app.core.auth.get_settings', return_value=mock_settings)

    # Valid key
    result = await validate_api_key("valid-key")
    assert result == "valid-key"

    # Invalid key
    with pytest.raises(HTTPException):
        await validate_api_key("invalid-key")
