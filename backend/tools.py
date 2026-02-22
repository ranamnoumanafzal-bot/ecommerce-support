import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from .database import SessionLocal, Order, Product, Return, Store, StoreSettings, Ticket, Conversation

def get_db():
    return SessionLocal()

def list_customer_orders(email: str) -> Dict[str, Any]:
    if not email or "@" not in email:
        return {"error": "Invalid email format provided.", "status": "failed"}
    db = get_db()
    try:
        orders = db.query(Order).filter(Order.customer_email == email).all()
        if not orders:
            return {"error": f"No orders found for '{email}'.", "status": "not_found"}
        
        return {
            "status": "success",
            "orders": [
                {
                    "order_id": o.id, 
                    "status": o.status, 
                    "order_date": o.order_date,
                    "total_amount": o.total_amount
                }
                for o in orders
            ]
        }
    except Exception as e:
        return {"error": f"Database error while listing orders: {str(e)}", "status": "error"}
    finally:
        db.close()

def get_order_details(order_id_or_tracking: str, email: str) -> Dict[str, Any]:
    if not order_id_or_tracking:
        return {"error": "Order ID or Tracking ID is required.", "status": "failed"}
    db = get_db()
    try:
        order = db.query(Order).filter(
            (Order.id == order_id_or_tracking) | 
            (Order.tracking_id == order_id_or_tracking)
        ).first()
        
        if not order:
            return {"error": f"Order with ID or Tracking ID '{order_id_or_tracking}' not found.", "status": "not_found"}
        
        if order.customer_email.lower() != email.lower():
            return {"error": "Account verification failed.", "status": "unauthorized"}
        
        store = db.query(Store).filter(Store.id == order.store_id).first()
        
        return {
            "status": "success",
            "order_id": order.id,
            "status_label": order.status,
            "order_date": order.order_date,
            "delivery_date": order.delivery_date,
            "total_amount": order.total_amount,
            "shipping_address": order.shipping_address,
            "tracking_id": order.tracking_id,
            "store_name": store.name if store else "Main Store"
        }
    except Exception as e:
        return {"error": f"Database error: {str(e)}", "status": "error"}
    finally:
        db.close()

def check_return_eligibility(order_id_or_tracking: str) -> Dict[str, Any]:
    db = get_db()
    try:
        order = db.query(Order).filter(
            (Order.id == order_id_or_tracking) | 
            (Order.tracking_id == order_id_or_tracking)
        ).first()
        
        if not order:
            return {"eligible": False, "reason": "Order not found.", "status": "not_found"}
        
        if order.status != 'delivered':
            return {"eligible": False, "reason": f"Order status is '{order.status}'. Needs to be 'delivered'.", "status": "invalid_state"}
        
        # DYNAMIC POLICY: Read from StoreSettings
        settings = db.query(StoreSettings).filter(StoreSettings.store_id == order.store_id).first()
        policy_days = settings.return_days_policy if settings else 7
        
        if not order.delivery_date:
            return {"eligible": False, "reason": "Delivery date missing.", "status": "data_error"}
        
        try:
            delivery_date = datetime.date.fromisoformat(order.delivery_date)
        except ValueError:
            return {"eligible": False, "reason": "Invalid date format.", "status": "data_error"}
            
        today = datetime.date.today()
        days_since_delivery = (today - delivery_date).days
        
        if days_since_delivery > policy_days:
            return {"eligible": False, "reason": f"Return window closed ({days_since_delivery} days since delivery, policy is {policy_days} days).", "status": "expired"}
        
        existing_return = db.query(Return).filter(Return.order_id == order.id).first()
        if existing_return:
            return {"eligible": False, "reason": "Return already requested.", "status": "duplicate"}
        
        return {"eligible": True, "reason": "Eligible for return.", "status": "success", "policy_limit": policy_days}
    except Exception as e:
        return {"eligible": False, "reason": f"System error: {str(e)}", "status": "error"}
    finally:
        db.close()

def cancel_order(order_id_or_tracking: str) -> Dict[str, Any]:
    db = get_db()
    try:
        order = db.query(Order).filter(
            (Order.id == order_id_or_tracking) | 
            (Order.tracking_id == order_id_or_tracking)
        ).first()
        
        if not order:
            return {"error": "Order not found.", "status": "not_found"}
        
        # DYNAMIC SETTING: Check if cancel is allowed
        settings = db.query(StoreSettings).filter(StoreSettings.store_id == order.store_id).first()
        if settings and not settings.allow_order_cancel:
            return {"error": "Cancellations are disabled for this store. Please contact support.", "status": "disabled"}

        if order.status != 'processing':
            return {"error": f"Cannot cancel order in '{order.status}' status.", "status": "invalid_state"}
        
        order.status = 'cancelled'
        db.commit()
        return {"success": True, "message": f"Order {order.id} cancelled.", "status": "success"}
    except Exception as e:
        db.rollback()
        return {"error": f"Failed: {str(e)}", "status": "error"}
    finally:
        db.close()

def create_support_ticket(conversation_id: str, email: str, reason: str) -> Dict[str, Any]:
    db = get_db()
    try:
        # Update conversation status to escalated
        conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.status = "escalated"
            
        ticket = Ticket(
            conversation_id=conversation_id,
            customer_email=email,
            reason=reason,
            status="open"
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return {
            "success": True,
            "ticket_id": ticket.id,
            "message": "A support ticket has been created and a human agent will take over shortly."
        }
    except Exception as e:
        db.rollback()
        return {"error": f"Failed: {str(e)}"}
    finally:
        db.close()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Get order details. Requires email for verification.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id_or_tracking": {"type": "string"},
                    "email": {"type": "string", "description": "Auto-filled by system"}
                },
                "required": ["order_id_or_tracking"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_return_eligibility",
            "description": "Check if an order is eligible for return based on store policy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id_or_tracking": {"type": "string"}
                },
                "required": ["order_id_or_tracking"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": "Cancel an order if allowed and in processing status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id_or_tracking": {"type": "string"}
                },
                "required": ["order_id_or_tracking"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_customer_orders",
            "description": "List all orders for a customer email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Auto-filled by system"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Create a support ticket for human escalation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "conversation_id": {"type": "string"},
                    "email": {"type": "string", "description": "Auto-filled by system"},
                    "reason": {"type": "string"}
                },
                "required": ["reason"]
            }
        }
    }
]

def call_tool(name: str, args: Dict[str, Any]) -> Any:
    if name == "get_order_details": return get_order_details(**args)
    if name == "check_return_eligibility": return check_return_eligibility(**args)
    if name == "cancel_order": return cancel_order(**args)
    if name == "list_customer_orders": return list_customer_orders(**args)
    if name == "create_support_ticket": return create_support_ticket(**args)
    return {"error": f"Tool {name} not found."}
