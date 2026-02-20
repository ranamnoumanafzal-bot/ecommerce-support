import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import database
from database import SessionLocal, Order, Product, Return, Store, SupportTicket

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
        # Search by Order ID OR Tracking ID
        order = db.query(Order).filter(
            (Order.id == order_id_or_tracking) | 
            (Order.tracking_id == order_id_or_tracking)
        ).first()
        
        if not order:
            return {"error": f"Order with ID or Tracking ID '{order_id_or_tracking}' not found.", "status": "not_found"}
        
        if order.customer_email.lower() != email.lower():
            return {"error": "Account verification failed. You can only access orders linked to your email address.", "status": "unauthorized"}
        
        # Get store info
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
        return {"error": f"Database error while fetching order details: {str(e)}", "status": "error"}
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
            return {"eligible": False, "reason": "Order not found in our system.", "status": "not_found"}
        
        if order.status != 'delivered':
            return {"eligible": False, "reason": f"Order is currently '{order.status}'. Only delivered orders can be returned.", "status": "invalid_state"}
        
        if not order.delivery_date:
            return {"eligible": False, "reason": "Delivery date record missing. Please contact support.", "status": "data_error"}
        
        # Get store policy
        store = db.query(Store).filter(Store.id == order.store_id).first()
        policy_days = store.return_days_policy if store else 7
        
        try:
            delivery_date = datetime.date.fromisoformat(order.delivery_date)
        except ValueError:
            return {"eligible": False, "reason": "Invalid delivery date format.", "status": "data_error"}
            
        today = datetime.date.today()
        days_since_delivery = (today - delivery_date).days
        
        if days_since_delivery > policy_days:
            return {"eligible": False, "reason": f"Return window closed. It has been {days_since_delivery} days since delivery (Policy limit: {policy_days} days).", "status": "expired"}
        
        # Check for existing return request
        existing_return = db.query(Return).filter(Return.order_id == order.id).first()
        if existing_return:
            return {"eligible": False, "reason": f"A return request already exists (Current status: {existing_return.status}).", "status": "duplicate"}
        
        return {"eligible": True, "reason": "Your order is eligible for a return.", "status": "success"}
    except Exception as e:
        return {"eligible": False, "reason": f"System error checking eligibility: {str(e)}", "status": "error"}
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
            return {"error": "Order not found."}
        
        if order.status != 'processing':
            return {"error": f"Order cannot be cancelled because its status is '{order.status}'. Only 'processing' orders can be cancelled."}
        
        order.status = 'cancelled'
        db.commit()
        
        return {"success": True, "message": f"Order {order.id} has been successfully cancelled."}
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to cancel order: {str(e)}"}
    finally:
        db.close()

def get_product_info(query: str) -> Dict[str, Any]:
    db = get_db()
    try:
        # Search by ID or Name
        product = db.query(Product).filter((Product.id == query) | (Product.name.ilike(f"%{query}%"))).first()
        
        if not product:
            return {"error": "Product not found."}
        
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "stock": product.stock,
            "store_id": product.store_id
        }
    finally:
        db.close()

def create_support_ticket(email: str, reason: str, conversation_summary: str) -> Dict[str, Any]:
    db = get_db()
    try:
        ticket = SupportTicket(
            customer_email=email,
            reason=reason,
            conversation_summary=conversation_summary,
            status="open"
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return {
            "success": True,
            "ticket_id": ticket.id,
            "message": f"Support ticket #{ticket.id} has been created. A human agent will review your case shortly."
        }
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to create support ticket: {str(e)}"}
    finally:
        db.close()

# Tool definitions for OpenAI function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Get status, dates, amount, address, and tracking for a specific order. Accepts Order ID or Tracking ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id_or_tracking": {"type": "string", "description": "The ID of the order or the Tracking ID."},
                    "email": {"type": "string", "description": "The customer's email address."}
                },
                "required": ["order_id_or_tracking", "email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_return_eligibility",
            "description": "Check if an order is eligible for a return. Accepts Order ID or Tracking ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id_or_tracking": {"type": "string", "description": "The ID of the order or the Tracking ID."}
                },
                "required": ["order_id_or_tracking"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_order",
            "description": "Cancel an order if it is still in 'processing'. Accepts Order ID or Tracking ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id_or_tracking": {"type": "string", "description": "The ID of the order or the Tracking ID."}
                },
                "required": ["order_id_or_tracking"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_product_info",
            "description": "Get details about a product including description, price, stock levels, and store ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The product ID or Name to search for."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_customer_orders",
            "description": "List all order IDs, status, date, and amount for a given customer email.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "The customer's email address."}
                },
                "required": ["email"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Escalate the issue to a human agent by creating a support ticket. Use this when the customer is angry, a refund is outside policy, there's a tool error, or fraud is suspected.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "The customer's email address."},
                    "reason": {"type": "string", "description": "The reason for escalation (e.g., 'Angry customer', 'Refund outside policy', 'Fraud suspicion')."},
                    "conversation_summary": {"type": "string", "description": "A brief summary of the conversation so far for the human agent."}
                },
                "required": ["email", "reason", "conversation_summary"]
            }
        }
    }
]

def call_tool(name: str, args: Dict[str, Any]) -> Any:
    if name == "get_order_details":
        return get_order_details(**args)
    elif name == "check_return_eligibility":
        return check_return_eligibility(**args)
    elif name == "cancel_order":
        return cancel_order(**args)
    elif name == "get_product_info":
        return get_product_info(**args)
    elif name == "list_customer_orders":
        return list_customer_orders(**args)
    elif name == "create_support_ticket":
        return create_support_ticket(**args)
    return {"error": f"Tool {name} not found."}
