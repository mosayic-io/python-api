"""Database-related test fixtures."""
import pytest


@pytest.fixture
def mock_supabase(mocker):
    """Mock Supabase client with successful responses"""
    mock_client = mocker.patch("app.core.supabase.supabase")
    
    # Create a generic successful response
    mock_response = mocker.Mock()
    mock_response.data = [{"id": 1, "name": "test"}]
    mock_response.count = 1
    mock_response.error = None
    
    # Chain mocks for typical Supabase query pattern
    mock_table = mocker.Mock()
    mock_select = mocker.Mock()
    mock_eq = mocker.Mock()
    mock_execute = mocker.Mock()
    
    mock_execute.return_value = mock_response
    mock_eq.execute = mock_execute
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    mock_client.table.return_value = mock_table
    
    return mock_client


@pytest.fixture
def mock_supabase_error(mocker):
    """Mock Supabase client with error responses"""
    mock_client = mocker.patch("app.core.supabase.supabase")
    
    mock_response = mocker.Mock()
    mock_response.data = None
    mock_response.error = {"message": "Database error", "code": "500"}
    mock_response.count = 0
    
    mock_table = mocker.Mock()
    mock_select = mocker.Mock()
    mock_eq = mocker.Mock()
    mock_execute = mocker.Mock()
    
    mock_execute.return_value = mock_response
    mock_eq.execute = mock_execute
    mock_select.eq.return_value = mock_eq
    mock_table.select.return_value = mock_select
    mock_client.table.return_value = mock_table
    
    return mock_client