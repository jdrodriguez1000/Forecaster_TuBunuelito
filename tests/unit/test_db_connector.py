import pytest
import os
from unittest.mock import patch, MagicMock
from src.connectors.db_connector import DBConnector

@pytest.fixture
def mock_env_vars():
    """Fixture to provide valid environment variables for success tests."""
    with patch.dict(os.environ, {
        "SUPABASE_URL": "https://example.supabase.co",
        "SUPABASE_KEY": "fake-key-123"
    }):
        yield

class TestDBConnector:
    """
    Unit tests for DBConnector using the 'Devil's Advocate' approach.
    Tests both happy paths and edge cases/failures.
    """

    @patch("src.connectors.db_connector.load_dotenv")
    def test_init_success(self, mock_load, mock_env_vars):
        """Test successful initialization when credentials are present."""
        connector = DBConnector()
        assert connector.url == "https://example.supabase.co"
        assert connector.key == "fake-key-123"

    @patch.dict(os.environ, {}, clear=True)
    @patch("src.connectors.db_connector.load_dotenv")
    def test_init_missing_credentials(self, mock_load):
        """Test failure when critical credentials are missing in the environment."""
        with pytest.raises(EnvironmentError) as excinfo:
            DBConnector()
        assert "Missing critical Supabase credentials" in str(excinfo.value)

    @patch.dict(os.environ, {"SUPABASE_URL": "https://example.supabase.co"}, clear=True)
    @patch("src.connectors.db_connector.load_dotenv")
    def test_init_missing_key_only(self, mock_load):
        """Test failure when only the KEY is missing."""
        with pytest.raises(EnvironmentError):
            DBConnector()

    @patch("src.connectors.db_connector.create_client")
    def test_get_client_singleton(self, mock_create, mock_env_vars):
        """
        Tests the Singleton pattern. 
        Multiple calls should return the same instance and only call create_client once.
        """
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        
        connector = DBConnector()
        client1 = connector.get_client()
        client2 = connector.get_client()
        
        assert client1 == client2
        assert client1 == mock_client
        mock_create.assert_called_once_with("https://example.supabase.co", "fake-key-123")

    @patch("src.connectors.db_connector.create_client")
    def test_get_client_critical_failure(self, mock_create, mock_env_vars):
        """Test behavior when the Supabase library fails to initialize (e.g., net error)."""
        mock_create.side_effect = Exception("Network unreachable")
        
        connector = DBConnector()
        with pytest.raises(Exception) as excinfo:
            connector.get_client()
        assert "Network unreachable" in str(excinfo.value)

    @patch("os.path.exists")
    @patch("src.connectors.db_connector.load_dotenv")
    def test_env_loading_fallback(self, mock_load, mock_exists, mock_env_vars):
        """Test that it falls back to default load_dotenv if custom path doesn't exist."""
        mock_exists.return_value = False
        
        DBConnector()
        # Verify load_dotenv was called without a specific path (default behavior)
        mock_load.assert_called_with()
