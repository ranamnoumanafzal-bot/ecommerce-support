# Ecommerce AI Support Agent

A web-based AI support agent built with FastAPI and OpenAI.

## Features
- **Track Order:** Verify order status and delivery dates.
- **Check Return Eligibility:** Automatic check based on delivery date (7-day window).
- **Cancel Order:** Cancel orders that are still in 'processing'.
- **Product Info:** Get descriptions, price, and stock for products.
- **Security Guardrails:** Multi-layer protection against prompt injection, sensitive data leakage, and automated escalation for negative customer sentiment.

## Guardrail Architecture
1. **Input Guardrails:** Pattern detection for prompt injection and suspicious commands.
2. **System Prompt Guardrails:** Strict behavioral rules embedded in the agent's core instructions.
3. **Tool Guardrails:** Deterministic business logic in tools that overrides AI decisions.
4. **Output Guardrails:** Filtering of sensitive technical data before it reaches the user.
5. **Escalation Guardrails:** Automatic handoff to human agents based on sentiment and message volume.

## Setup
1. **Initialize Database:**
   ```bash
   python init_db.py
   ```
2. **Set OpenAI API Key:**
   Create a `.env` file in the root directory and add your key:
   ```
   OPENAI_API_KEY=your_real_api_key_here
   ```
3. **Install Dependencies:**
   ```bash
   python -m pip install -r requirements.txt
   ```

## Running the App
1. **Start Backend:**
   ```bash
   python backend/main.py
   ```
   The backend will run on `http://localhost:8000`.

2. **Open Frontend:**
   Simply open `frontend/index.html` in your browser.

## Test Data
- **Email:** `user@example.com`
- **Orders:**
  - `o1`: Shipped, 2 days ago.
  - `o2`: Delivered, 10 days ago (Ineligible for return).
  - `o4`: Delivered, 3 days ago (Eligible for return).
- **Email:** `test@test.com`
  - `o3`: Processing (Can be cancelled).
