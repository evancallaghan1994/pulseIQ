from sqlalchemy import (
    Boolean, Column, Date, DateTime, Integer, Text, VARCHAR,
    ForeignKey, func
)
from db.connection import Base


class Rep(Base):
    __tablename__ = "reps"

    rep_id       = Column(VARCHAR(10),  primary_key=True)
    name         = Column(VARCHAR(100), nullable=False)
    hire_date    = Column(Date,         nullable=False)
    territory    = Column(VARCHAR(50),  nullable=False)
    annual_quota = Column(Integer,      nullable=False)


class Lead(Base):
    __tablename__ = "leads"

    lead_id          = Column(VARCHAR(10),  primary_key=True)
    source           = Column(VARCHAR(30),  nullable=False)
    created_at       = Column(Date,         nullable=False)
    company_size     = Column(VARCHAR(10),  nullable=False)
    industry         = Column(VARCHAR(30),  nullable=False)
    converted        = Column(Boolean,      nullable=False)
    converted_at     = Column(Date)
    conversion_value = Column(Integer)


class Deal(Base):
    __tablename__ = "deals"

    deal_id           = Column(VARCHAR(10), primary_key=True)
    lead_id           = Column(VARCHAR(10), ForeignKey("leads.lead_id"), nullable=False)
    rep_id            = Column(VARCHAR(10), ForeignKey("reps.rep_id"),   nullable=False)
    product           = Column(VARCHAR(60), nullable=False)
    stage             = Column(VARCHAR(20), nullable=False)
    created_at        = Column(Date,        nullable=False)
    last_contact_date = Column(Date,        nullable=False)
    close_date        = Column(Date)
    value             = Column(Integer,     nullable=False)
    outcome           = Column(VARCHAR(20), nullable=False)


class Engagement(Base):
    __tablename__ = "engagement"

    event_id   = Column(VARCHAR(10), primary_key=True)
    deal_id    = Column(VARCHAR(10), ForeignKey("deals.deal_id"), nullable=False)
    event_type = Column(VARCHAR(20), nullable=False)
    timestamp  = Column(Date,        nullable=False)
    channel    = Column(VARCHAR(20), nullable=False)


class Customer(Base):
    __tablename__ = "customers"

    customer_id       = Column(VARCHAR(10),  primary_key=True)
    company_name      = Column(VARCHAR(100), nullable=False)
    subscription_tier = Column(VARCHAR(20),  nullable=False)
    mrr               = Column(Integer,      nullable=False)
    start_date        = Column(Date,         nullable=False)
    churn_date        = Column(Date)
    churn_reason      = Column(VARCHAR(30))


class Insight(Base):
    __tablename__ = "insights"

    id           = Column(Integer,      primary_key=True, autoincrement=True)
    generated_at = Column(DateTime,     nullable=False, server_default=func.now())
    insight_type = Column(VARCHAR(50),  nullable=False)
    summary      = Column(Text,         nullable=False)
    data_snapshot = Column(Text)
