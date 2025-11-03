import uuid
from datetime import UTC, datetime
from unittest.mock import patch

from fastapi import status

from src.core.app_status import ApplicationStatus
from src.models.application import Applications


class TestApplicationEndpoints:
    def test_create_application_success(self, client, db_session, mock_kafka_producer):
        # Test data
        application_data = {
            "pan_number": "ABCDE1234F",
            "applicant_name": "John Doe",
            "monthly_income_inr": 50000.00,
            "loan_amount_inr": 200000.00,
            "loan_type": "PERSONAL",
        }

        # Make the request
        response = client.post("/applications/", json=application_data)

        # Check response
        assert response.status_code == status.HTTP_202_ACCEPTED
        response_data = response.json()
        assert "application_id" in response_data
        assert response_data["status"] == ApplicationStatus.PENDING.value
        assert response_data["message"] == "Application created successfully"

        # Verify database entry
        db_application = (
            db_session.query(Applications)
            .filter(Applications.id == uuid.UUID(response_data["application_id"]))
            .first()
        )

        assert db_application is not None
        assert db_application.pan_number == application_data["pan_number"]
        assert db_application.applicant_name == application_data["applicant_name"]
        assert (
            float(db_application.monthly_income_inr)
            == application_data["monthly_income_inr"]
        )
        assert (
            float(db_application.loan_amount_inr) == application_data["loan_amount_inr"]
        )
        assert db_application.loan_type == application_data["loan_type"]
        assert db_application.status == ApplicationStatus.PENDING.value

        # Verify Kafka message was sent
        mock_kafka_producer.assert_called_once()

    def test_create_application_invalid_data(self, client):
        # Test with invalid PAN number format
        invalid_data = {
            "pan_number": "INVALID",  # Invalid format
            "applicant_name": "John Doe",
            "monthly_income_inr": 50000.00,
            "loan_amount_inr": 200000.00,
            "loan_type": "PERSONAL",
        }

        response = client.post("/applications/", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test with missing required field
        incomplete_data = {
            "pan_number": "ABCDE1234F",
            "applicant_name": "John Doe",
            # monthly_income_inr is missing
            "loan_amount_inr": 200000.00,
            "loan_type": "PERSONAL",
        }

        response = client.post("/applications/", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_application_kafka_failure(self, client, db_session):
        # Test data
        application_data = {
            "pan_number": "ABCDE1234F",
            "applicant_name": "John Doe",
            "monthly_income_inr": 50000.00,
            "loan_amount_inr": 200000.00,
            "loan_type": "PERSONAL",
        }

        # Mock Kafka producer to return False (failure)
        with patch(
            "src.kafka.kafka_producer.MessageProducer.produce_message",
            return_value=False,
        ):
            response = client.post("/applications/", json=application_data)

        # Even if Kafka fails, the API should still return success
        assert response.status_code == status.HTTP_202_ACCEPTED
        response_data = response.json()
        assert "application_id" in response_data

        # Verify database entry was still created
        db_application = (
            db_session.query(Applications)
            .filter(Applications.id == uuid.UUID(response_data["application_id"]))
            .first()
        )

        assert db_application is not None

    def test_get_application_status_success(self, client, db_session):
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

        # Make the request
        response = client.get(f"/applications/{test_id}/status")

        # Check response
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["application_id"] == str(test_id)
        assert response_data["status"] == ApplicationStatus.PENDING.value

    def test_get_application_status_not_found(self, client):
        # Generate a random UUID that doesn't exist in the database
        non_existent_id = uuid.uuid4()

        # Make the request
        response = client.get(f"/applications/{non_existent_id}/status")

        # Check response
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert (
            "Application with ID " + str(non_existent_id) + " not found"
            in response.json()["detail"]
        )
