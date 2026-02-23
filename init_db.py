import datetime
from backend.database import engine, Base, SessionLocal, Store, Product, Order, Return, StoreSettings, User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_db():
    print("Dropping and recreating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Seed Stores
        main_store = Store(
            id="s1",
            name="Main Electronics Store",
            support_email="support@mainstore.com"
        )
        db.add(main_store)
        
        # Seed Store Settings
        settings = StoreSettings(
            store_id="s1",
            return_days_policy=15, # Extended to 15 days
            allow_order_cancel=True,
            tone="friendly",
            escalation_threshold=5
        )
        db.add(settings)

        # Seed Admin User
        admin_user = User(
            email="admin@example.com",
            hashed_password=pwd_context.hash("admin123"),
            is_verified=True
        )
        db.add(admin_user)
        
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
                order_date=(today - datetime.timedelta(days=20)).isoformat(), # Old order
                delivery_date=(today - datetime.timedelta(days=18)).isoformat(),
                shipping_address="123 AI Street, Tech City",
                tracking_id="TRK789012"
            )
        ]
        db.add_all(orders)
        
        db.commit()
        print("Database initialized successfully with the Professional Architecture schema.")
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
