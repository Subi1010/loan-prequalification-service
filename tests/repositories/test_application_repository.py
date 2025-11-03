import uuid
from datetime import UTC, datetime

from src.core.app_status import ApplicationStatus
from src.models.application import Applications
from src.repositories.application_repository import ApplicationRepository
from src.schemas.application import ApplicationCreate


class TestApplicationRepository:
    """Tests for the ApplicationRepository class"""

    def test_create(self, db_session):
        """Test creating a new application"""
        # Create test data
        application_data = ApplicationCreate(
            pan_number="ABCDE1234F",
            applicant_name="John Doe",
            monthly_income_inr=50000.00,
            loan_amount_inr=200000.00,
            loan_type="PERSONAL",
        )

        # Create repository and call method
        repository = ApplicationRepository(db_session)
        result = repository.create(application_data)

        # Verify result
        assert result is not None
        assert result.id is not None
        assert result.pan_number == application_data.pan_number
        assert result.applicant_name == application_data.applicant_name
        assert float(result.monthly_income_inr) == application_data.monthly_income_inr
        assert float(result.loan_amount_inr) == application_data.loan_amount_inr
        assert result.loan_type == application_data.loan_type
        assert result.status == ApplicationStatus.PENDING.value
        assert result.created_at is not None
        assert result.updated_at is not None

        # Verify database state
        db_application = (
            db_session.query(Applications).filter(Applications.id == result.id).first()
        )
        assert db_application is not None
        assert db_application.id == result.id

    def test_get_by_id_found(self, db_session):
        """Test retrieving an application by ID when it exists"""
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

        # Create repository and call method
        repository = ApplicationRepository(db_session)
        result = repository.get_by_id(test_id)

        # Verify result
        assert result is not None
        assert result.id == test_id
        assert result.pan_number == test_application.pan_number
        assert result.applicant_name == test_application.applicant_name

    def test_get_by_id_not_found(self, db_session):
        """Test retrieving an application by ID when it doesn't exist"""
        # Generate a random UUID that doesn't exist in the database
        non_existent_id = uuid.uuid4()

        # Create repository and call method
        repository = ApplicationRepository(db_session)
        result = repository.get_by_id(non_existent_id)

        # Verify result
        assert result is None

    def test_update_cibil_and_status_found(self, db_session):
        """Test updating CIBIL score and status when application exists"""
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

        # Create repository and call method
        repository = ApplicationRepository(db_session)
        result = repository.update_cibil_and_status(
            test_id, 750, ApplicationStatus.PRE_APPROVED
        )

        # Verify result
        assert result is not None
        assert result.id == test_id
        assert result.cibil_score == 750
        assert result.status == ApplicationStatus.PRE_APPROVED.value

        # Verify database state
        db_application = (
            db_session.query(Applications).filter(Applications.id == test_id).first()
        )
        assert db_application is not None
        assert db_application.cibil_score == 750
        assert db_application.status == ApplicationStatus.PRE_APPROVED.value

    def test_update_cibil_and_status_not_found(self, db_session):
        """Test updating CIBIL score and status when application doesn't exist"""
        # Generate a random UUID that doesn't exist in the database
        non_existent_id = uuid.uuid4()

        # Create repository and call method
        repository = ApplicationRepository(db_session)
        result = repository.update_cibil_and_status(
            non_existent_id, 750, ApplicationStatus.PRE_APPROVED
        )

        # Verify result
        assert result is None
