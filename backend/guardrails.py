import re
from typing import Dict, Any, List, Optional
import json

class GuardrailResponse:
    def __init__(self, safe: bool, reason: Optional[str] = None, action: Optional[str] = None):
        self.safe = safe
        self.reason = reason
        self.action = action

# 1. Input Guardrails
def check_input_guardrails(text: str) -> GuardrailResponse:
    # Pattern 1: Prompt Injection Attempts
    injection_patterns = [
        r"ignore previous instructions",
        r"disregard all rules",
        r"you are now a",
        r"system override",
        r"<script>",
        r"DROP TABLE",
        r"DELETE FROM",
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return GuardrailResponse(False, "Suspicious activity detected in input.", "block")

    # Pattern 2: PII (Personal Identifiable Information) - Simple version
    # credit_card_pattern = r"\b(?:\d[ -]*?){13,16}\b"
    # if re.search(credit_card_pattern, text):
    #     return GuardrailResponse(False, "Please do not share credit card details.", "mask")

    return GuardrailResponse(True)

# 4. Output Guardrails
def check_output_guardrails(text: str) -> str:
    # Remove sensitive data pattern
    # Example: Hide internal IDs or database error messages if they leaked
    sensitive_patterns = [
        (r'database_error: .*', 'An internal error occurred.'),
        (r'SQL STATE: \d+', '[REDACTED]'),
    ]
    
    filtered_text = text
    for pattern, replacement in sensitive_patterns:
        filtered_text = re.sub(pattern, replacement, filtered_text, flags=re.IGNORECASE)
        
    return filtered_text

# 6. Escalation Guardrail (Sentiment based)
def should_escalate(text: str, message_count: int) -> bool:
    negative_keywords = [
        "angry", "scam", "sue", "lawyer", "terrible", "worst", 
        "disappointed", "frustrated", "manager", "stolen"
    ]
    
    # Check for negative keywords
    count = 0
    for word in negative_keywords:
        if word in text.lower():
            count += 1
            
    # Trigger escalation if multiple negative words or message count is high
    if count >= 2 or message_count > 10:
        return True
        
    return False

# Role-Based Guardrails (Simplified)
def verify_access(user_role: str, action: str) -> bool:
    role_permissions = {
        "admin": ["view_analytics", "refund_order", "list_tickets", "takeover"],
        "customer": ["chat", "list_orders", "check_status"]
    }
    
    return action in role_permissions.get(user_role, [])
