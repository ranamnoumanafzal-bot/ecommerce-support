from sqlalchemy import create_engine, Column, String, Integer, Float, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

# If DATABASE_URL is not set, default to SQLite for local development
# Format for Postgres: postgresql://user:password@localhost:5432/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")

# For SQLite, we need to allow multi-threading
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False, "timeout": 30} if DATABASE_URL.startswith("sqlite") else {"connect_timeout": 10},
    pool_pre_ping=True,
    pool_recycle=3600
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Store(Base):
    __tablename__ = "stores"
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    return_days_policy = Column(Integer, default=7)
    support_email = Column(String)
    
    products = relationship("Product", back_populates="store")
    orders = relationship("Order", back_populates="store")

class Product(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float)
    stock = Column(Integer)
    
    store = relationship("Store", back_populates="products")

class Order(Base):
    __tablename__ = "orders"
    id = Column(String, primary_key=True, index=True)
    store_id = Column(String, ForeignKey("stores.id"))
    customer_email = Column(String, index=True)
    status = Column(String) # processing, shipped, delivered, cancelled
    total_amount = Column(Float)
    order_date = Column(String) # ISO 8601 string
    delivery_date = Column(String, nullable=True) # ISO 8601 string
    shipping_address = Column(Text)
    tracking_id = Column(String, nullable=True)
    
    store = relationship("Store", back_populates="orders")
    returns = relationship("Return", back_populates="order")

class Return(Base):
    __tablename__ = "returns"
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id"))
    status = Column(String) # requested, approved, rejected, completed
    created_at = Column(String)
    
    order = relationship("Order", back_populates="returns")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, index=True)
    role = Column(String) # system, user, assistant, tool
    content = Column(Text, nullable=True)
    tool_call_id = Column(String, nullable=True)
    name = Column(String, nullable=True) # For tool role
    tool_calls_json = Column(Text, nullable=True) # For assistant role with tool calls
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_email = Column(String, index=True)
    reason = Column(String)
    conversation_summary = Column(Text)
    status = Column(String, default="open") # open, in_progress, resolved
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
