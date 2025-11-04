"""
Tests for the health check endpoints.
"""

from unittest.mock import patch

from fastapi import status

from src.core.database import check_database_health


class TestHealthEndpoints:
    """Tests for the health check endpoints."""

    def test_health_check_success(self, client):
        """Test health check endpoint when all systems are healthy."""
        # Mock the database health check to return success
        with patch(
            "src.api.health.check_database_health", return_value={"database": True}
        ):
            # Make the request
            response = client.get("/health/")

            # Check response
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert "database" in response_data
            assert response_data["database"] is True

    def test_health_check_database_failure(self, client):
        """Test health check endpoint when database is unhealthy."""
        # Mock the database health check to return failure
        with patch(
            "src.api.health.check_database_health", return_value={"database": False}
        ):
            # Make the request
            response = client.get("/health/")

            # Check response
            assert response.status_code == status.HTTP_200_OK
            response_data = response.json()
            assert "database" in response_data
            assert response_data["database"] is False

    def test_database_health_check_function(self):
        """Test the database health check function directly."""
        # Mock the database session to simulate success
        with patch("src.core.database.SessionLocal") as mock_session:
            # Configure the mock to simulate a successful database connection
            mock_db = mock_session.return_value
            mock_db.execute.return_value = True

            # Call the function
            result = check_database_health()

            # Verify the result
            assert result == {"database": True}
            mock_db.execute.assert_called_once()
            mock_db.close.assert_called_once()

    def test_database_health_check_function_failure(self):
        """Test the database health check function when database connection fails."""
        # Mock the database session to simulate failure
        with patch("src.core.database.SessionLocal") as mock_session:
            # Configure the mock to simulate a database connection failure
            mock_db = mock_session.return_value
            mock_db.execute.side_effect = Exception("Database connection error")

            # Call the function
            result = check_database_health()

            # Verify the result
            assert result == {"database": False}
            mock_db.execute.assert_called_once()
            mock_db.close.assert_called_once()

    def test_database_health_check_function_session_creation_failure(self):
        """Test the database health check function when session creation fails."""
        # Mock the database session to simulate session creation failure
        with patch(
            "src.core.database.SessionLocal",
            side_effect=Exception("Session creation error"),
        ):
            # Call the function
            result = check_database_health()

            # Verify the result
            assert result == {"database": False}
