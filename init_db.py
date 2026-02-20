import datetime
from backend.database import engine, Base, SessionLocal, Store, Product, Order, Return

def init_db():
    # Create tables
    Base.metadata.drop_all(bind=engine) # Start fresh for the new schema
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Seed Stores
        main_store = Store(
            id="s1",
            name="Main Electronics Store",
            return_days_policy=7,
            support_email="support@mainstore.com"
        )
        db.add(main_store)
        
        # Seed Products
        products = [
            Product(id="p1", store_id="s1", name="Wireless Headphones", description="High-quality noise-canceling headphones", price=199.99, stock=50),
            Product(id="p2", store_id="s1", name="Smart Watch", description="Feature-rich smartwatch with heart rate monitor", price=149.50, stock=30),
            Product(id="p3", store_id="s1", name="Leather Wallet", description="Slim genuine leather wallet", price=45.00, stock=100)
        ]
        db.add_all(products)

        today = datetime.date.today()
        
        # Seed Orders
        orders = [
            Order(
                id="o1", 
                store_id="s1", 
                customer_email="user@example.com", 
                status="shipped", 
                total_amount=199.99, 
                order_date=(today - datetime.timedelta(days=2)).isoformat(),
                shipping_address="123 AI Street, Tech City",
                tracking_id="TRK123456"
            ),
            Order(
                id="o2", 
                store_id="s1", 
                customer_email="user@example.com", 
                status="delivered", 
                total_amount=149.50, 
                order_date=(today - datetime.timedelta(days=10)).isoformat(),
                delivery_date=(today - datetime.timedelta(days=8)).isoformat(),
                shipping_address="123 AI Street, Tech City",
                tracking_id="TRK789012"
            ),
            Order(
                id="o3", 
                store_id="s1", 
                customer_email="test@test.com", 
                status="processing", 
                total_amount=45.00, 
                order_date=today.isoformat(),
                shipping_address="456 Beta Road, Dev Town"
            ),
            Order(
                id="o4", 
                store_id="s1", 
                customer_email="user@example.com", 
                status="delivered", 
                total_amount=199.99, 
                order_date=(today - datetime.timedelta(days=3)).isoformat(),
                delivery_date=(today - datetime.timedelta(days=2)).isoformat(),
                shipping_address="123 AI Street, Tech City",
                tracking_id="TRK345678"
            )
        ]
        db.add_all(orders)
        
        # Seed Returns
        db.add(Return(
            order_id="o2",
            status="completed",
            created_at=(today - datetime.timedelta(days=7)).isoformat()
        ))

        db.commit()
        print("Database initialized successfully with the new scalable schema.")
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
