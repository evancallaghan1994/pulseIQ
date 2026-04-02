-- PulseIQ Database Schema
-- Run once to initialize all tables. Safe to re-run (IF NOT EXISTS).

-- Reps
CREATE TABLE IF NOT EXISTS reps (
    rep_id          VARCHAR(10)     PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    hire_date       DATE            NOT NULL,
    territory       VARCHAR(50)     NOT NULL,
    annual_quota    INTEGER         NOT NULL
);

-- Leads
CREATE TABLE IF NOT EXISTS leads (
    lead_id             VARCHAR(10)     PRIMARY KEY,
    source              VARCHAR(30)     NOT NULL,
    created_at          DATE            NOT NULL,
    company_size        VARCHAR(10)     NOT NULL,
    industry            VARCHAR(30)     NOT NULL,
    converted           BOOLEAN         NOT NULL,
    converted_at        DATE,
    conversion_value    INTEGER
);

CREATE INDEX IF NOT EXISTS idx_leads_created_at  ON leads (created_at);
CREATE INDEX IF NOT EXISTS idx_leads_converted   ON leads (converted);

-- Deals
CREATE TABLE IF NOT EXISTS deals (
    deal_id             VARCHAR(10)     PRIMARY KEY,
    lead_id             VARCHAR(10)     NOT NULL REFERENCES leads (lead_id),
    rep_id              VARCHAR(10)     NOT NULL REFERENCES reps (rep_id),
    product             VARCHAR(60)     NOT NULL,
    stage               VARCHAR(20)     NOT NULL,
    created_at          DATE            NOT NULL,
    last_contact_date   DATE            NOT NULL,
    close_date          DATE,
    value               INTEGER         NOT NULL,
    outcome             VARCHAR(20)     NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_deals_rep_id     ON deals (rep_id);
CREATE INDEX IF NOT EXISTS idx_deals_lead_id    ON deals (lead_id);
CREATE INDEX IF NOT EXISTS idx_deals_created_at ON deals (created_at);
CREATE INDEX IF NOT EXISTS idx_deals_outcome    ON deals (outcome);

-- Engagement
CREATE TABLE IF NOT EXISTS engagement (
    event_id    VARCHAR(10)     PRIMARY KEY,
    deal_id     VARCHAR(10)     NOT NULL REFERENCES deals (deal_id),
    event_type  VARCHAR(20)     NOT NULL,
    timestamp   DATE            NOT NULL,
    channel     VARCHAR(20)     NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_engagement_deal_id   ON engagement (deal_id);
CREATE INDEX IF NOT EXISTS idx_engagement_timestamp ON engagement (timestamp);

-- Customers
CREATE TABLE IF NOT EXISTS customers (
    customer_id         VARCHAR(10)     PRIMARY KEY,
    company_name        VARCHAR(100)    NOT NULL,
    subscription_tier   VARCHAR(20)     NOT NULL,
    mrr                 INTEGER         NOT NULL,
    start_date          DATE            NOT NULL,
    churn_date          DATE,
    churn_reason        VARCHAR(30)
);

CREATE INDEX IF NOT EXISTS idx_customers_tier       ON customers (subscription_tier);
CREATE INDEX IF NOT EXISTS idx_customers_start_date ON customers (start_date);

-- Insights (written by the autonomous insight agent)
CREATE TABLE IF NOT EXISTS insights (
    id              SERIAL          PRIMARY KEY,
    generated_at    TIMESTAMP       NOT NULL DEFAULT NOW(),
    insight_type    VARCHAR(50)     NOT NULL,
    summary         TEXT            NOT NULL,
    data_snapshot   TEXT
);

CREATE INDEX IF NOT EXISTS idx_insights_generated_at ON insights (generated_at);
