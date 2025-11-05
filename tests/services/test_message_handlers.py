from src.services.credit_service import handle_application_event
from src.services.decision_service import handle_cibil_score_event
from src.services.message_handlers import TOPIC_HANDLERS


class TestMessageHandlers:
    def test_topic_handlers_mapping(self):
        # Verify the mapping for loan_applications_submitted
        assert "loan_applications_submitted" in TOPIC_HANDLERS
        assert TOPIC_HANDLERS["loan_applications_submitted"] == handle_application_event

        # Verify the mapping for credit_reports_generated
        assert "credit_reports_generated" in TOPIC_HANDLERS
        assert TOPIC_HANDLERS["credit_reports_generated"] == handle_cibil_score_event

        # Verify there are exactly 2 handlers
        assert len(TOPIC_HANDLERS) == 2

    def test_topic_handlers_functions_exist(self):
        # Verify that handle_application_event is callable
        assert callable(TOPIC_HANDLERS["loan_applications_submitted"])

        # Verify that handle_cibil_score_event is callable
        assert callable(TOPIC_HANDLERS["credit_reports_generated"])
