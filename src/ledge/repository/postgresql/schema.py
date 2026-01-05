SCHEMAS = """CREATE TYPE account_status_enum AS ENUM (
    'open',
    'close'
);
CREATE TYPE account_type_enum AS ENUM (
    'asset',
    'liability',
    'equity',
    'income',
    'expense'
);

CREATE TABLE commodity (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    prefix boolean NOT NULL,
    description TEXT
);
CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type account_type_enum NOT NULL,
    open boolean NOT NULL DEFAULT TRUE,
    commodity_id INTEGER REFERENCES commodity(id)
);
CREATE TABLE account_statuses (
    id SERIAL PRIMARY KEY,
    status account_status_enum NOT NULL,
    date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    account_id INTEGER NOT NULL REFERENCES accounts(id)
);
CREATE INDEX idx_account_status_account_id ON account_statuses(account_id);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    description TEXT
);
CREATE TABLE splits (
    id SERIAL PRIMARY KEY,
    amount NUMERIC NOT NULL,

    commodity_id INTEGER NOT NULL REFERENCES commodity(id),
    account_id INTEGER NOT NULL REFERENCES accounts(id),
    transaction_id INTEGER NOT NULL REFERENCES transactions(id)
);

CREATE INDEX idx_splits_account_id ON splits(account_id);
CREATE INDEX idx_splits_transaction_id ON splits(transaction_id);
CREATE INDEX idx_splits_commodity_id ON splits(commodity_id);
CREATE INDEX idx_transactions_date ON transactions(date);"""
