-- Initialize database schema for fintech fraud detection

CREATE TABLE IF NOT EXISTS transactions (
  transaction_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  event_time TIMESTAMP NOT NULL,
  merchant_category TEXT,
  amount NUMERIC,
  location TEXT,
  processing_time TIMESTAMP DEFAULT now()
);

CREATE TABLE IF NOT EXISTS fraud_alerts (
  alert_id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  transaction_id TEXT,
  fraud_type TEXT,
  detection_time TIMESTAMP DEFAULT now(),
  details JSONB
);

CREATE TABLE IF NOT EXISTS validated_transactions (
  transaction_id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  event_time TIMESTAMP NOT NULL,
  merchant_category TEXT,
  amount NUMERIC,
  location TEXT,
  processing_time TIMESTAMP
);
