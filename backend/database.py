from sqlalchemy import create_engine, Column, String, Integer, Float, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os
import datetime
from dotenv import load_dotenv

load_dotenv()

# If DATABASE_URL is not set, default to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ecommerce.db")

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
    support_email = Column(String)
    
    products = relationship("Product", back_populates="store")
    orders = relationship("Order", back_populates="store")
    settings = relationship("StoreSettings", back_populates="store", uselist=False)

class StoreSettings(Base):
    __tablename__ = "store_settings"
    store_id = Column(String, ForeignKey("stores.id"), primary_key=True)
    return_days_policy = Column(Integer, default=7)
    allow_order_cancel = Column(Boolean, default=True)
    tone = Column(String, default="friendly") # formal, friendly
    escalation_threshold = Column(Integer, default=5) # e.g., max messages before suggesting escalation

    store = relationship("Store", back_populates="settings")

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

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(String, primary_key=True, index=True)
    customer_email = Column(String, index=True)
    channel = Column(String, default="web")
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="open") # open, escalated, closed
    
    messages = relationship("Message", back_populates="conversation")
    tickets = relationship("Ticket", back_populates="conversation")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    sender = Column(String) # user, agent, human, system
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    # Fields for tool integration (storing tool outputs/calls)
    tool_call_id = Column(String, nullable=True)
    name = Column(String, nullable=True)
    tool_calls_json = Column(Text, nullable=True)

    conversation = relationship("Conversation", back_populates="messages")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    customer_email = Column(String, index=True)
    reason = Column(String)
    status = Column(String, default="open") # open, resolved
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="tickets")

class ConversationAnalytics(Base):
    __tablename__ = "conversation_analytics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, unique=True, index=True)
    customer_email = Column(String, index=True)
    intent = Column(String, nullable=True)
    tool_calls_count = Column(Integer, default=0)
    message_count = Column(Integer, default=0)
    was_escalated = Column(Boolean, default=False)
    resolution_type = Column(String, default="pending")
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# User table for authentication
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=True)
    otp_code = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
