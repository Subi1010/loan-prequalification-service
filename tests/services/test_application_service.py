import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from src.core.app_status import ApplicationStatus
from src.models.application import Applications
from src.repositories.application_repository import ApplicationRepository
from src.schemas.application import ApplicationCreate, ApplicationStatusResponse
from src.services.application_service import ApplicationService


class TestApplicationService:
    """Tests for the ApplicationService class"""

    def test_create_application_success(self, db_session, mock_kafka_producer):
        """Test creating a new application with successful Kafka publishing"""
        # Create test data
        application_data = ApplicationCreate(
            pan_number="ABCDE1234F",
            applicant_name="John Doe",
            monthly_income_inr=50000.00,
            loan_amount_inr=200000.00,
            loan_type="PERSONAL",
        )

        # Create service and call method
        service = ApplicationService(db_session)
        result = service.create_application(application_data, "test_topic")

        # Verify result
        assert result is not None
        assert result.id is not None
        assert result.pan_number == application_data.pan_number
        assert result.applicant_name == application_data.applicant_name
        assert float(result.monthly_income_inr) == application_data.monthly_income_inr
        assert float(result.loan_amount_inr) == application_data.loan_amount_inr
        assert result.loan_type == application_data.loan_type
        assert result.status == ApplicationStatus.PENDING.value

        # Verify Kafka message was sent
        mock_kafka_producer.assert_called_once()
        args, kwargs = mock_kafka_producer.call_args
        assert args[0] == "test_topic"
        assert args[1] == str(result.id)
        assert "id" in args[2]
        assert "pan_number" in args[2]
        assert "applicant_name" in args[2]
        assert "monthly_income_inr" in args[2]
        assert "loan_amount_inr" in args[2]
        assert "loan_type" in args[2]
        assert "status" in args[2]
        assert "created_at" in args[2]
        assert "updated_at" in args[2]

    def test_create_application_kafka_failure(self, db_session):
        """Test creating a new application with Kafka publishing failure"""
        # Create test data
        application_data = ApplicationCreate(
            pan_number="ABCDE1234F",
            applicant_name="John Doe",
            monthly_income_inr=50000.00,
            loan_amount_inr=200000.00,
            loan_type="PERSONAL",
        )

        # Mock Kafka producer to return False (failure)
        with patch(
            "src.kafka.kafka_producer.MessageProducer.produce_message",
            return_value=False,
        ):
            # Create service and call method
            service = ApplicationService(db_session)
            result = service.create_application(application_data, "test_topic")

            # Verify result (application should still be created even if Kafka fails)
            assert result is not None
            assert result.id is not None
            assert result.pan_number == application_data.pan_number
            assert result.status == ApplicationStatus.PENDING.value

    def test_get_application_status_found(self, db_session):
        """Test retrieving application status when application exists"""
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

        # Create service and call method
        service = ApplicationService(db_session)
        result = service.get_application_status(test_id)

        # Verify result
        assert result is not None
        assert isinstance(result, ApplicationStatusResponse)
        assert result.application_id == test_id
        assert result.status == ApplicationStatus.PENDING.value

    def test_get_application_status_not_found(self, db_session):
        """Test retrieving application status when application doesn't exist"""
        # Generate a random UUID that doesn't exist in the database
        non_existent_id = uuid.uuid4()

        # Create service and call method
        service = ApplicationService(db_session)
        result = service.get_application_status(non_existent_id)

        # Verify result
        assert result is None

    def test_prepare_kafka_message(self):
        """Test preparing Kafka message from application data"""
        # Create a test application
        test_id = uuid.uuid4()
        created_at = datetime.now(UTC)
        updated_at = datetime.now(UTC)
        test_application = Applications(
            id=test_id,
            pan_number="ABCDE1234F",
            applicant_name="John Doe",
            monthly_income_inr=50000.00,
            loan_amount_inr=200000.00,
            loan_type="PERSONAL",
            status=ApplicationStatus.PENDING.value,
            created_at=created_at,
            updated_at=updated_at,
        )

        # Call the method
        result = ApplicationService._prepare_kafka_message(test_application)

        # Verify result
        assert result is not None
        assert result["id"] == str(test_id)
        assert result["pan_number"] == "ABCDE1234F"
        assert result["applicant_name"] == "John Doe"
        assert result["monthly_income_inr"] == 50000.00
        assert result["loan_amount_inr"] == 200000.00
        assert result["loan_type"] == "PERSONAL"
        assert result["status"] == ApplicationStatus.PENDING.value
        assert result["created_at"] == created_at.isoformat()
        assert result["updated_at"] == updated_at.isoformat()

    def test_repository_integration(self, db_session):
        """Test that the service correctly uses the repository"""
        # Create a mock repository
        mock_repository = MagicMock(spec=ApplicationRepository)
        mock_repository.create.return_value = Applications(
            id=uuid.uuid4(),
            pan_number="ABCDE1234F",
            applicant_name="John Doe",
            monthly_income_inr=50000.00,
            loan_amount_inr=200000.00,
            loan_type="PERSONAL",
            status=ApplicationStatus.PENDING.value,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Create test data
        application_data = ApplicationCreate(
            pan_number="ABCDE1234F",
            applicant_name="John Doe",
            monthly_income_inr=50000.00,
            loan_amount_inr=200000.00,
            loan_type="PERSONAL",
        )

        # Create service with mock repository
        with (
            patch(
                "src.services.application_service.ApplicationRepository",
                return_value=mock_repository,
            ),
            patch(
                "src.kafka.kafka_producer.MessageProducer.produce_message",
                return_value=True,
            ),
        ):
            service = ApplicationService(db_session)
            service.create_application(application_data, "test_topic")

            # Verify repository method was called
            mock_repository.create.assert_called_once()
            args, kwargs = mock_repository.create.call_args
            assert args[0] == application_data
