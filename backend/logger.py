import logging
import os
from datetime import datetime

# Build paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_FILE = os.path.join(BASE_DIR, "production.log")

# Configure format
log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("EcommerceAgent")

def log_api_error(endpoint: str, error: str, context: dict = None):
    msg = f"API Error at {endpoint}: {error}"
    if context:
        msg += f" | Context: {context}"
    logger.error(msg)

def log_ai_failure(model: str, error: str):
    logger.critical(f"AI Model Failure ({model}): {error}")

def log_db_timeout(operation: str):
    logger.warning(f"Database Timeout/Latency during: {operation}")

def log_user_input(session_id: str, message: str):
    # Log incoming messages for auditing (Careful with PII in real production)
    logger.info(f"User [{session_id}]: {message[:100]}...")

def log_system_event(event: str):
    logger.info(f"System Event: {event}")
