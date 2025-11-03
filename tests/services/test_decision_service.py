import json
import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from src.core.app_status import ApplicationStatus
from src.models.application import Applications
from src.services.decision_service import DecisionService, handle_cibil_score_event


class TestDecisionService:
    """Tests for the decision service module"""

    def test_process_decision_application_not_found(self, db_session):
        """Test process_decision when application is not found"""
        # Generate a random UUID that doesn't exist in the database
        application_id = uuid.uuid4()

        # Call the function
        result = DecisionService.process_decision(
            application_id,
            700,
            {"monthly_income_inr": 50000, "loan_amount_inr": 200000},
        )

        # Verify the result
        assert result is False

    def test_process_decision_rejected(self, db_session):
        """Test process_decision with low CIBIL score (rejected)"""
        # Create a test application in the database
        test_id = uuid.uuid4()
        test_application = Applications(
            id=test_id,
            pan_number="ABCDE1234F",
            applicant_name="John Doe",
            monthly_income_inr=50000.00,
            loan_amount_inr=200000.00,
            loan_type="PERSONAL",
            status=ApplicationStatus.PENDING.value,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(test_application)
        db_session.commit()

        # Mock the SessionLocal to return our test db_session
        mock_session = MagicMock()
        mock_session.return_value = db_session

        # Mock the ApplicationRepository
        mock_repository = MagicMock()
        mock_repository.update_cibil_and_status.return_value = test_application

        with (
            patch("src.services.decision_service.SessionLocal", mock_session),
            patch(
                "src.services.decision_service.ApplicationRepository",
                return_value=mock_repository,
            ),
        ):
            # Call the function with a low CIBIL score
            result = DecisionService.process_decision(
                test_id,
                600,
                {"monthly_income_inr": 50000, "loan_amount_inr": 200000},
            )

            # Verify the result
            assert result is True

            # Verify the repository was called with the correct parameters
            mock_repository.update_cibil_and_status.assert_called_once()
            args, kwargs = mock_repository.update_cibil_and_status.call_args
            assert args[0] == test_id
            assert args[1] == 600
            assert args[2] == ApplicationStatus.REJECTED

    def test_process_decision_pre_approved(self, db_session):
        """Test process_decision with high CIBIL score and good income (pre-approved)"""
        # Create a test application in the database
        test_id = uuid.uuid4()
        test_application = Applications(
            id=test_id,
            pan_number="ABCDE1234F",
            applicant_name="John Doe",
            monthly_income_inr=50000.00,
            loan_amount_inr=200000.00,
            loan_type="PERSONAL",
            status=ApplicationStatus.PENDING.value,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(test_application)
        db_session.commit()

        # Mock the SessionLocal to return our test db_session
        mock_session = MagicMock()
        mock_session.return_value = db_session

        # Mock the ApplicationRepository
        mock_repository = MagicMock()
        mock_repository.update_cibil_and_status.return_value = test_application

        with (
            patch("src.services.decision_service.SessionLocal", mock_session),
            patch(
                "src.services.decision_service.ApplicationRepository",
                return_value=mock_repository,
            ),
        ):
            # Call the function with a high CIBIL score and good income
            # Loan amount / 48 = 4166.67, which is less than monthly income of 50000
            result = DecisionService.process_decision(
                test_id,
                700,
                {"monthly_income_inr": 50000, "loan_amount_inr": 200000},
            )

            # Verify the result
            assert result is True

            # Verify the repository was called with the correct parameters
            mock_repository.update_cibil_and_status.assert_called_once()
            args, kwargs = mock_repository.update_cibil_and_status.call_args
            assert args[0] == test_id
            assert args[1] == 700
            assert args[2] == ApplicationStatus.PRE_APPROVED

    def test_process_decision_manual_review(self, db_session):
        """Test process_decision with high CIBIL score but low income (manual review)"""
        # Create a test application in the database
        test_id = uuid.uuid4()
        test_application = Applications(
            id=test_id,
            pan_number="ABCDE1234F",
            applicant_name="John Doe",
            monthly_income_inr=10000.00,
            loan_amount_inr=1000000.00,
            loan_type="PERSONAL",
            status=ApplicationStatus.PENDING.value,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(test_application)
        db_session.commit()

        # Mock the SessionLocal to return our test db_session
        mock_session = MagicMock()
        mock_session.return_value = db_session

        # Mock the ApplicationRepository
        mock_repository = MagicMock()
        mock_repository.update_cibil_and_status.return_value = test_application

        with (
            patch("src.services.decision_service.SessionLocal", mock_session),
            patch(
                "src.services.decision_service.ApplicationRepository",
                return_value=mock_repository,
            ),
        ):
            # Call the function with a high CIBIL score but low income
            # Loan amount / 48 = 20833.33, which is more than monthly income of 10000
            result = DecisionService.process_decision(
                test_id,
                700,
                {"monthly_income_inr": 10000, "loan_amount_inr": 1000000},
            )

            # Verify the result
            assert result is True

            # Verify the repository was called with the correct parameters
            mock_repository.update_cibil_and_status.assert_called_once()
            args, kwargs = mock_repository.update_cibil_and_status.call_args
            assert args[0] == test_id
            assert args[1] == 700
            assert args[2] == ApplicationStatus.MANUAL_REVIEW

    def test_process_decision_string_uuid(self, db_session):
        """Test process_decision with string UUID"""
        # Create a test application in the database
        test_id = uuid.uuid4()
        test_application = Applications(
            id=test_id,
            pan_number="ABCDE1234F",
            applicant_name="John Doe",
            monthly_income_inr=50000.00,
            loan_amount_inr=200000.00,
            loan_type="PERSONAL",
            status=ApplicationStatus.PENDING.value,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        db_session.add(test_application)
        db_session.commit()

        # Mock the SessionLocal to return our test db_session
        mock_session = MagicMock()
        mock_session.return_value = db_session

        # Mock the ApplicationRepository
        mock_repository = MagicMock()
        mock_repository.update_cibil_and_status.return_value = test_application

        with (
            patch("src.services.decision_service.SessionLocal", mock_session),
            patch(
                "src.services.decision_service.ApplicationRepository",
                return_value=mock_repository,
            ),
        ):
            # Call the function with a string UUID
            result = DecisionService.process_decision(
                str(test_id),
                700,
                {"monthly_income_inr": 50000, "loan_amount_inr": 200000},
            )

            # Verify the result
            assert result is True

            # Verify the repository was called with the correct parameters
            mock_repository.update_cibil_and_status.assert_called_once()
            args, kwargs = mock_repository.update_cibil_and_status.call_args
            # First argument should be a UUID object converted from the string
            assert isinstance(args[0], uuid.UUID)
            assert args[0] == test_id
            assert args[1] == 700
            assert args[2] == ApplicationStatus.PRE_APPROVED

    def test_process_decision_exception(self, db_session):
        """Test process_decision with exception"""
        # Create a test application in the database
        test_id = uuid.uuid4()

        # Create a mock db object
        mock_db = MagicMock()

        # Mock the ApplicationRepository to raise an exception
        mock_repository = MagicMock()
        mock_repository.update_cibil_and_status.side_effect = Exception(
            "Test exception"
        )

        # Patch SessionLocal to return our mock db
        with (
            patch("src.services.decision_service.SessionLocal", return_value=mock_db),
            patch(
                "src.services.decision_service.ApplicationRepository",
                return_value=mock_repository,
            ),
        ):
            # Call the function
            result = DecisionService.process_decision(
                test_id,
                700,
                {"monthly_income_inr": 50000, "loan_amount_inr": 200000},
            )

            # Verify the result
            assert result is False

            # Verify the db.close was called
            mock_db.close.assert_called_once()

    def test_handle_cibil_score_event_success(self):
        """Test successful handling of CIBIL score event"""
        # Create a mock message
        mock_message = MagicMock()
        mock_message.value = json.dumps(
            {
                "application_id": "123e4567-e89b-12d3-a456-426614174000",
                "cibil_score": 700,
                "application_data": {
                    "monthly_income_inr": 50000,
                    "loan_amount_inr": 200000,
                },
            }
        ).encode("utf-8")

        # Mock the DecisionService.process_decision method
        with patch(
            "src.services.decision_service.DecisionService.process_decision",
            return_value=True,
        ):
            # Call the function
            result = handle_cibil_score_event(mock_message)

            # Verify the result
            assert result is True

    def test_handle_cibil_score_event_missing_data(self):
        """Test handling of CIBIL score event with missing data"""
        # Create a mock message with missing CIBIL score
        mock_message = MagicMock()
        mock_message.value = json.dumps(
            {
                "application_id": "123e4567-e89b-12d3-a456-426614174000",
                "application_data": {
                    "monthly_income_inr": 50000,
                    "loan_amount_inr": 200000,
                },
            }
        ).encode("utf-8")

        # Call the function
        result = handle_cibil_score_event(mock_message)

        # Verify the result
        assert result is False

        # Create a mock message with missing application ID
        mock_message.value = json.dumps(
            {
                "cibil_score": 700,
                "application_data": {
                    "monthly_income_inr": 50000,
                    "loan_amount_inr": 200000,
                },
            }
        ).encode("utf-8")

        # Call the function
        result = handle_cibil_score_event(mock_message)

        # Verify the result
        assert result is False

    def test_handle_cibil_score_event_exception(self):
        """Test handling of CIBIL score event with exception"""
        # Create a mock message
        mock_message = MagicMock()
        mock_message.value = b"invalid json"

        # Call the function
        result = handle_cibil_score_event(mock_message)

        # Verify the result
        assert result is False

    def test_handle_cibil_score_event_process_decision_failure(self):
        """Test handling of CIBIL score event with process_decision failure"""
        # Create a mock message
        mock_message = MagicMock()
        mock_message.value = json.dumps(
            {
                "application_id": "123e4567-e89b-12d3-a456-426614174000",
                "cibil_score": 700,
                "application_data": {
                    "monthly_income_inr": 50000,
                    "loan_amount_inr": 200000,
                },
            }
        ).encode("utf-8")

        # Mock the DecisionService.process_decision method to return False (failure)
        with patch(
            "src.services.decision_service.DecisionService.process_decision",
            return_value=False,
        ):
            # Call the function
            result = handle_cibil_score_event(mock_message)

            # Verify the result
            assert result is False
