from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    account_name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)
    account_subtype = Column(String, nullable=True)
    account_role = Column(String, nullable=True)  # "Spending", "Bills Reserve", "Savings"
    current_balance = Column(Float, default=0.0)
    available_balance = Column(Float, default=0.0)
    plaid_account_id = Column(String, nullable=True)
    institution_name = Column(String, nullable=True)
    last_synced = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class AccountSnapshot(Base):
    __tablename__ = "account_snapshots"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    balance = Column(Float, nullable=False)
    snapshot_date = Column(Date, nullable=False)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    plaid_transaction_id = Column(String, unique=True, nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    merchant = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=True)
    transaction_date = Column(Date, nullable=False)
    is_pending = Column(Boolean, default=False)
    notes = Column(String, nullable=True)


class Bill(Base):
    __tablename__ = "bills"

    id = Column(Integer, primary_key=True)
    bill_name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    frequency = Column(String, nullable=False, default="Monthly")
    notes = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)


class BillPayment(Base):
    __tablename__ = "bill_payments"

    id = Column(Integer, primary_key=True)
    bill_id = Column(Integer, ForeignKey("bills.id"), nullable=False)
    amount = Column(Float, nullable=False)
    paid_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=True)


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True)
    goal_name = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(Date, nullable=False)
    notes = Column(String, nullable=True)


class GoalDeposit(Base):
    __tablename__ = "goal_deposits"

    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    amount = Column(Float, nullable=False)
    deposit_date = Column(Date, nullable=False)


class WishlistItem(Base):
    __tablename__ = "wishlist"

    id = Column(Integer, primary_key=True)
    item_name = Column(String, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    current_saved = Column(Float, default=0.0)
    planned_purchase_date = Column(Date, nullable=True)
    priority = Column(String, default="Medium")
    status = Column(String, default="Planning")
    notes = Column(String, nullable=True)


class WishlistDeposit(Base):
    __tablename__ = "wishlist_deposits"

    id = Column(Integer, primary_key=True)
    wishlist_id = Column(Integer, ForeignKey("wishlist.id"), nullable=False)
    amount = Column(Float, nullable=False)
    deposit_date = Column(Date, nullable=False)


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    setting_name = Column(String, unique=True, nullable=False)
    setting_value = Column(String, nullable=True)
