import pytest
from backend import tools
from backend.database import Order, Store, StoreSettings
import datetime

def test_check_return_eligibility_expired(db_session):
    # Setup
    store = Store(id="s1", name="Test Store")
    db_session.add(store)
    
    settings = StoreSettings(store_id="s1", return_days_policy=7)
    db_session.add(settings)
    
    today = datetime.date.today()
    order = Order(
        id="o_old",
        store_id="s1",
        customer_email="test@example.com",
        status="delivered",
        delivery_date=(today - datetime.timedelta(days=10)).isoformat(),
        order_date=(today - datetime.timedelta(days=12)).isoformat()
    )
    db_session.add(order)
    db_session.commit()

    # We need to mock get_db inside tools or make tools accept a db session
    # Currently tools.py has its own get_db()
    
    # Let's temporarily patch tools.get_db to return our test db_session
    original_get_db = tools.get_db
    tools.get_db = lambda: db_session
    
    try:
        result = tools.check_return_eligibility("o_old")
        assert result["eligible"] is False
        assert "closed" in result["reason"]
    finally:
        tools.get_db = original_get_db

def test_cancel_order_valid(db_session):
    store = Store(id="s2", name="Test Store 2")
    db_session.add(store)
    db_session.add(StoreSettings(store_id="s2", allow_order_cancel=True))
    
    order = Order(id="o_proc", store_id="s2", status="processing", customer_email="t2@ex.com")
    db_session.add(order)
    db_session.commit()

    original_get_db = tools.get_db
    tools.get_db = lambda: db_session
    
    try:
        result = tools.cancel_order("o_proc")
        assert result["success"] is True
        assert order.status == "cancelled"
    finally:
        tools.get_db = original_get_db
