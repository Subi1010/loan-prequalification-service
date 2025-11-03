import json
from unittest.mock import MagicMock, patch

from src.services.credit_service import CreditScoreService, handle_application_event


class TestCreditService:
    def test_calculate_cibil_score_specific_pan(self):
        # Test with specific PAN numbers that have hardcoded scores
        assert (
            CreditScoreService.calculate_cibil_score({"pan_number": "ABCDE1234F"})
            == 790
        )
        assert (
            CreditScoreService.calculate_cibil_score({"pan_number": "FGHIJ5678K"})
            == 610
        )

    def test_calculate_cibil_score_high_income(self):
        # Test with high income
        with patch("random.randint", return_value=0):  # Remove randomness for testing
            score = CreditScoreService.calculate_cibil_score(
                {"monthly_income_inr": 100000, "loan_type": "PERSONAL"}
            )
            # Base (650) + Income bonus (40) + Loan type penalty (-10) + Random (0) = 680
            assert score == 680

    def test_calculate_cibil_score_low_income(self):
        # Test with low income
        with patch("random.randint", return_value=0):  # Remove randomness for testing
            score = CreditScoreService.calculate_cibil_score(
                {"monthly_income_inr": 25000, "loan_type": "HOME"}
            )
            # Base (650) + Income penalty (-20) + Loan type bonus (10) + Random (0) = 640
            assert score == 640

    def test_calculate_cibil_score_medium_income(self):
        # Test with medium income (no adjustment)
        with patch("random.randint", return_value=0):  # Remove randomness for testing
            score = CreditScoreService.calculate_cibil_score(
                {"monthly_income_inr": 50000, "loan_type": "OTHER"}
            )
            # Base (650) + Income (0) + Loan type (0) + Random (0) = 650
            assert score == 650

    def test_calculate_cibil_score_random_factor(self):
        # Test with random factor
        with patch("random.randint", return_value=5):  # Set random factor to 5
            score = CreditScoreService.calculate_cibil_score(
                {"monthly_income_inr": 50000, "loan_type": "OTHER"}
            )
            # Base (650) + Income (0) + Loan type (0) + Random (5) = 655
            assert score == 655

    def test_calculate_cibil_score_bounds(self):
        # Test lower bound (score should not go below 300)
        with patch("random.randint", return_value=-500):  # Try to force score below 300
            score = CreditScoreService.calculate_cibil_score(
                {"monthly_income_inr": 10000, "loan_type": "PERSONAL"}
            )
            assert score == 300

        # Test upper bound (score should not go above 900)
        with patch("random.randint", return_value=500):  # Try to force score above 900
            score = CreditScoreService.calculate_cibil_score(
                {"monthly_income_inr": 100000, "loan_type": "HOME"}
            )
            assert score == 900

    def test_handle_application_event_success(self):
        # Create a mock message
        mock_message = MagicMock()
        mock_message.value = json.dumps(
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "pan_number": "ABCDE1234F",
                "monthly_income_inr": 50000,
                "loan_type": "PERSONAL",
            }
        ).encode("utf-8")

        # Mock the CreditScoreService.calculate_cibil_score method and Mock the MessageProducer.produce_message method
        with (
            patch(
                "src.services.credit_service.CreditScoreService.calculate_cibil_score",
                return_value=750,
            ),
            patch(
                "src.services.credit_service.MessageProducer.produce_message",
                return_value=True,
            ),
        ):
            # Call the function
            result = handle_application_event(mock_message)

            # Verify the result
            assert result is True

    def test_handle_application_event_missing_id(self):
        # Create a mock message with missing ID
        mock_message = MagicMock()
        mock_message.value = json.dumps(
            {
                "pan_number": "ABCDE1234F",
                "monthly_income_inr": 50000,
                "loan_type": "PERSONAL",
            }
        ).encode("utf-8")

        # Call the function
        result = handle_application_event(mock_message)

        # Verify the result
        assert result is False

    def test_handle_application_event_exception(self):
        """Test handling of application event with exception"""
        # Create a mock message
        mock_message = MagicMock()
        mock_message.value = b"invalid json"

        # Call the function
        result = handle_application_event(mock_message)

        # Verify the result
        assert result is False

    def test_handle_application_event_kafka_failure(self):
        """Test handling of application event with Kafka failure"""
        # Create a mock message
        mock_message = MagicMock()
        mock_message.value = json.dumps(
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "pan_number": "ABCDE1234F",
                "monthly_income_inr": 50000,
                "loan_type": "PERSONAL",
            }
        ).encode("utf-8")

        # Mock the CreditScoreService.calculate_cibil_score method and Mock the MessageProducer.produce_message method to return False (failure)
        with (
            patch(
                "src.services.credit_service.CreditScoreService.calculate_cibil_score",
                return_value=750,
            ),
            patch(
                "src.services.credit_service.MessageProducer.produce_message",
                return_value=False,
            ),
        ):
            # Call the function
            result = handle_application_event(mock_message)

            # Verify the result
            assert result is True  # The function still returns True even if Kafka fails
