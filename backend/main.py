from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

import tools

load_dotenv()

app = FastAPI(title="Ecommerce AI Support Agent")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use Hugging Face OpenAI-compatible endpoint
client = OpenAI(
    base_url="https://router.huggingface.co/v1/",
    api_key=os.getenv("HUGGINGFACE_API_KEY")
)

# Use a model that supports Tool Calling (Qwen 2.5 is excellent for this)
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"

class ChatRequest(BaseModel):
    message: str
    customer_email: str
    session_id: Optional[str] = "default"

class ChatResponse(BaseModel):
    response: str
    session_id: str

SYSTEM_PROMPT = """
You are a professional ecommerce support assistant named EcommerceSupportAgent.

You now have access to a scalable database with multi-store support.
Always verify order ownership (check if the order belongs to the customer's email) before sharing details.
If a customer asks about their orders but doesn't provide an order ID, use the 'list_customer_orders' tool with their email to find their orders first.
Always use tools when needed to fetch real-time data.
You can now provide detailed order information including:
- Order Status and History
- Total Amount
- Shipping Address and Tracking ID
- Store-specific return policies (check return eligibility tool)

Follow the return policy provided by the 'check_return_eligibility' tool, as it now accounts for store-specific policies.

HUMAN ESCALATION:
Use the 'create_support_ticket' tool to escalate to a human agent in the following cases:
1. Customer is extremely angry, frustrated, or abusive.
2. Customer requests a refund or return that is strictly outside the calculated policy but insists on it.
3. You encounter a technical error or the customer reports a major bug.
4. You suspect fraudulent activity.
5. The customer's request is beyond your capabilities or scope.

Be polite, concise, and helpful.
"""

from database import SessionLocal, ChatMessage

def save_message(db, session_id, role, content=None, tool_call_id=None, name=None, tool_calls_json=None):
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        tool_call_id=tool_call_id,
        name=name,
        tool_calls_json=tool_calls_json
    )
    db.add(msg)
    db.commit()

def get_session_messages(db, session_id, limit=10):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.id.desc()).limit(limit).all()
    messages.reverse()
    
    formatted_messages = []
    for m in messages:
        msg = {"role": m.role}
        if m.content is not None:
            msg["content"] = m.content
        if m.name:
            msg["name"] = m.name
        if m.tool_call_id:
            msg["tool_call_id"] = m.tool_call_id
        if m.tool_calls_json:
            msg["tool_calls"] = json.loads(m.tool_calls_json)
        formatted_messages.append(msg)
    return formatted_messages

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id
    db = SessionLocal()
    
    try:
        # Load last 10 messages from DB
        history = get_session_messages(db, session_id, limit=10)
        
        if not history:
            # Initialize with system prompt if new session
            save_message(db, session_id, "system", SYSTEM_PROMPT)
            history = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add email context for internal tracking (optional, but keep for consistency with previous logic)
        user_context = f"\n[System Context: Customer Email is {request.customer_email}]"
        user_content = request.message + user_context
        
        # Save and append user message
        save_message(db, session_id, "user", user_content)
        history.append({"role": "user", "content": user_content})
        
        # Initial call to LLM
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=history,
            tools=tools.TOOLS,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        # Handle tool calls
        if tool_calls:
            # Save assistant message with tool calls
            tool_calls_list = []
            for tc in tool_calls:
                tool_calls_list.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })
            
            save_message(db, session_id, "assistant", content=response_message.content, tool_calls_json=json.dumps(tool_calls_list))
            history.append(response_message)
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                if function_name == "get_order_details" and "email" not in function_args:
                    function_args["email"] = request.customer_email
                
                print(f"Calling tool: {function_name} with {function_args}")
                tool_response = tools.call_tool(function_name, function_args)
                
                # Save and append tool response
                tool_content = json.dumps(tool_response)
                save_message(db, session_id, "tool", content=tool_content, tool_call_id=tool_call.id, name=function_name)
                
                history.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": tool_content
                })
            
            # Get final response from LLM
            second_response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=history
            )
            final_message = second_response.choices[0].message.content
            save_message(db, session_id, "assistant", final_message)
            return ChatResponse(response=final_message, session_id=session_id)
        
        else:
            final_message = response.choices[0].message.content
            save_message(db, session_id, "assistant", final_message)
            return ChatResponse(response=final_message, session_id=session_id)

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    import traceback
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception:
        traceback.print_exc()
