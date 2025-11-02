from src.services.credit_service import handle_application_event
from src.services.decision_service import handle_cibil_score_event

TOPIC_HANDLERS = {
    "loan_applications_submitted": handle_application_event,
    "credit_reports_generated": handle_cibil_score_event,
}
