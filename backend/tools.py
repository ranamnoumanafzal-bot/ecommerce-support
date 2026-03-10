import os
import httpx
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

try:
    from . import logger
except ImportError:
    import logger

NODE_BACKEND_URL = os.getenv("NODE_BACKEND_URL", "http://localhost:5000/api/v1")
API_KEY = os.getenv("AI_AGENT_API_KEY")

async def call_node_api(method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, Any]:
    """Helper to call the MERN backend with security headers."""
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    url = f"{NODE_BACKEND_URL}{endpoint}"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            if method.upper() == "GET":
                response = await client.get(url, params=params, headers=headers)
            else:
                response = await client.post(url, json=data, headers=headers)
            
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"error": f"Backend API error: {e.response.text}", "status": "error"}
        except Exception as e:
            return {"error": f"Connection failed: {str(e)}", "status": "error"}

async def list_customer_orders(email: str) -> Dict[str, Any]:
    if not email or "@" not in email:
        return {"error": "Invalid email format.", "status": "failed"}
    return await call_node_api("GET", "/orders", params={"email": email})

async def get_order_details(order_id_or_tracking: str, email: str) -> Dict[str, Any]:
    if not order_id_or_tracking:
        return {"error": "Order ID required.", "status": "failed"}
    return await call_node_api("GET", f"/orders/{order_id_or_tracking}", params={"email": email})

async def check_return_eligibility(order_id_or_tracking: str) -> Dict[str, Any]:
    return await call_node_api("GET", f"/orders/{order_id_or_tracking}/return-eligibility")

async def cancel_order(order_id_or_tracking: str) -> Dict[str, Any]:
    return await call_node_api("POST", f"/orders/{order_id_or_tracking}/cancel")

async def search_products(query: str) -> Dict[str, Any]:
    return await call_node_api("GET", "/products/search", params={"query": query})

async def create_support_ticket(conversation_id: str, email: str, reason: str) -> Dict[str, Any]:
    # conversation_id is handled locally or passed to node
    return await call_node_api("POST", "/tickets", data={
        "email": email,
        "reason": f"Ticket from AI (ID: {conversation_id}): {reason}"
    })

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_order_details",
            "description": "Get order details including status and delivery date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id_or_tracking": {"type": "string"},
                    "email": {"type": "string"}
                },
                "required": ["order_id_or_tracking"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_return_eligibility",
            "description": "Check if an order can be returned.",
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
            "description": "Request cancellation of an order.",
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
            "name": "search_products",
            "description": "Search for products by name or description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_customer_orders",
            "description": "List history of orders for a customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_support_ticket",
            "description": "Escalate to a human agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string"}
                },
                "required": ["reason"]
            }
        }
    }
]

async def call_tool(name: str, args: Dict[str, Any]) -> Any:
    # Note: These are now async functions
    if name == "get_order_details": return await get_order_details(**args)
    if name == "check_return_eligibility": return await check_return_eligibility(**args)
    if name == "cancel_order": return await cancel_order(**args)
    if name == "list_customer_orders": return await list_customer_orders(**args)
    if name == "search_products": return await search_products(**args)
    if name == "create_support_ticket": return await create_support_ticket(**args)
    return {"error": f"Tool {name} not found."}
