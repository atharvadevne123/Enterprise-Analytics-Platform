-- Unified Enterprise Analytics Data Warehouse Schema
-- Support for E-Commerce, Supply Chain, and Financial Analytics

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- Dimension: Products (E-Commerce)
CREATE TABLE IF NOT EXISTS public.dim_products (
    product_id BIGINT PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    subcategory VARCHAR(100),
    supplier_id BIGINT,
    cost DECIMAL(10, 2),
    list_price DECIMAL(10, 2),
    current_stock_level INT DEFAULT 0,
    reorder_point INT DEFAULT 100,
    lead_time_days INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Customers (E-Commerce)
CREATE TABLE IF NOT EXISTS public.dim_customers (
    customer_id BIGINT PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(20),
    segment VARCHAR(50),  -- VIP, Regular, New, Inactive
    lifetime_value DECIMAL(15, 2) DEFAULT 0,
    country VARCHAR(100),
    region VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Suppliers (Supply Chain)
CREATE TABLE IF NOT EXISTS public.dim_suppliers (
    supplier_id BIGINT PRIMARY KEY,
    supplier_name VARCHAR(255) NOT NULL,
    country VARCHAR(100),
    region VARCHAR(100),
    on_time_delivery_pct DECIMAL(5, 2) DEFAULT 0,
    quality_score DECIMAL(5, 2) DEFAULT 0,
    lead_time_days INT,
    contract_start_date DATE,
    contract_end_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    payment_terms VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: GL Accounts (Financial)
CREATE TABLE IF NOT EXISTS public.dim_gl_accounts (
    gl_account_id VARCHAR(20) PRIMARY KEY,
    account_name VARCHAR(255) NOT NULL,
    account_type VARCHAR(50),  -- Asset, Liability, Equity, Revenue, Expense
    account_subtype VARCHAR(50),  -- Detailed classification
    department VARCHAR(100),
    cost_center VARCHAR(50),
    is_balance_sheet BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dimension: Date (Conformed)
CREATE TABLE IF NOT EXISTS public.dim_dates (
    date_id INT PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    year INT,
    quarter INT,
    month INT,
    week INT,
    day_of_month INT,
    day_of_week INT,
    day_name VARCHAR(20),
    month_name VARCHAR(20),
    is_weekend BOOLEAN,
    is_holiday BOOLEAN DEFAULT FALSE
);

-- ============================================================================
-- FACT TABLES
-- ============================================================================

-- Fact: Orders (E-Commerce)
CREATE TABLE IF NOT EXISTS public.fact_orders (
    order_id BIGINT PRIMARY KEY,
    order_date_id INT NOT NULL REFERENCES public.dim_dates(date_id),
    customer_id BIGINT NOT NULL REFERENCES public.dim_customers(customer_id),
    product_id BIGINT NOT NULL REFERENCES public.dim_products(product_id),
    supplier_id BIGINT REFERENCES public.dim_suppliers(supplier_id),

    quantity INT NOT NULL,
    list_price DECIMAL(10, 2),
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    order_amount DECIMAL(12, 2),
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    shipping_amount DECIMAL(10, 2) DEFAULT 0,
    total_amount DECIMAL(12, 2),

    cost_amount DECIMAL(10, 2),
    gross_profit DECIMAL(12, 2),
    gross_margin_pct DECIMAL(5, 2),

    order_status VARCHAR(50),  -- Pending, Shipped, Delivered, Cancelled
    payment_status VARCHAR(50),  -- Pending, Paid, Refunded
    shipping_status VARCHAR(50),  -- Processing, Shipped, In Transit, Delivered

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_order_date FOREIGN KEY (order_date_id) REFERENCES public.dim_dates(date_id)
);

CREATE INDEX idx_fact_orders_customer ON public.fact_orders(customer_id);
CREATE INDEX idx_fact_orders_product ON public.fact_orders(product_id);
CREATE INDEX idx_fact_orders_order_date ON public.fact_orders(order_date_id);

-- Fact: Transactions (Financial)
CREATE TABLE IF NOT EXISTS public.fact_transactions (
    transaction_id BIGINT PRIMARY KEY,
    transaction_date_id INT NOT NULL REFERENCES public.dim_dates(date_id),
    gl_account_id VARCHAR(20) NOT NULL REFERENCES public.dim_gl_accounts(gl_account_id),

    debit_amount DECIMAL(15, 2) DEFAULT 0,
    credit_amount DECIMAL(15, 2) DEFAULT 0,
    net_amount DECIMAL(15, 2),

    transaction_type VARCHAR(50),  -- Journal Entry, Invoice, Payment, etc.
    description VARCHAR(500),
    reference_id VARCHAR(100),  -- Order ID, PO ID, etc.

    currency_code VARCHAR(3),
    exchange_rate DECIMAL(10, 6) DEFAULT 1.0,

    is_intercompany BOOLEAN DEFAULT FALSE,
    is_reconciled BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_transaction_date FOREIGN KEY (transaction_date_id) REFERENCES public.dim_dates(date_id),
    CONSTRAINT fk_transaction_gl FOREIGN KEY (gl_account_id) REFERENCES public.dim_gl_accounts(gl_account_id)
);

CREATE INDEX idx_fact_transactions_date ON public.fact_transactions(transaction_date_id);
CREATE INDEX idx_fact_transactions_gl ON public.fact_transactions(gl_account_id);

-- Fact: Deliveries (Supply Chain)
CREATE TABLE IF NOT EXISTS public.fact_deliveries (
    delivery_id BIGINT PRIMARY KEY,
    po_id BIGINT NOT NULL,
    supplier_id BIGINT NOT NULL REFERENCES public.dim_suppliers(supplier_id),
    product_id BIGINT NOT NULL REFERENCES public.dim_products(product_id),

    order_date_id INT NOT NULL REFERENCES public.dim_dates(date_id),
    delivery_date_id INT REFERENCES public.dim_dates(date_id),
    promised_date_id INT REFERENCES public.dim_dates(date_id),

    quantity_ordered INT,
    quantity_delivered INT,
    quantity_rejected INT DEFAULT 0,

    unit_cost DECIMAL(10, 2),
    total_cost DECIMAL(12, 2),

    lead_time_days INT,
    is_on_time BOOLEAN,
    is_quality_pass BOOLEAN DEFAULT TRUE,

    delivery_status VARCHAR(50),  -- Pending, In Transit, Delivered, Cancelled

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_delivery_supplier FOREIGN KEY (supplier_id) REFERENCES public.dim_suppliers(supplier_id),
    CONSTRAINT fk_delivery_product FOREIGN KEY (product_id) REFERENCES public.dim_products(product_id),
    CONSTRAINT fk_delivery_order_date FOREIGN KEY (order_date_id) REFERENCES public.dim_dates(date_id)
);

CREATE INDEX idx_fact_deliveries_supplier ON public.fact_deliveries(supplier_id);
CREATE INDEX idx_fact_deliveries_product ON public.fact_deliveries(product_id);

-- Fact: Budgets vs Actuals (Financial)
CREATE TABLE IF NOT EXISTS public.fact_budget_actuals (
    budget_id BIGINT PRIMARY KEY,
    gl_account_id VARCHAR(20) NOT NULL REFERENCES public.dim_gl_accounts(gl_account_id),
    date_id INT NOT NULL REFERENCES public.dim_dates(date_id),

    budget_amount DECIMAL(15, 2),
    actual_amount DECIMAL(15, 2),
    variance_amount DECIMAL(15, 2),
    variance_pct DECIMAL(5, 2),

    budget_type VARCHAR(50),  -- Monthly, Quarterly, Annual
    budget_version INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_budget_gl FOREIGN KEY (gl_account_id) REFERENCES public.dim_gl_accounts(gl_account_id),
    CONSTRAINT fk_budget_date FOREIGN KEY (date_id) REFERENCES public.dim_dates(date_id)
);

-- ============================================================================
-- ANALYTICS MARTS (Aggregated Views)
-- ============================================================================

-- E-Commerce Analytics Mart
CREATE TABLE IF NOT EXISTS analytics.ecommerce_daily_metrics (
    date_id INT PRIMARY KEY,
    total_orders INT DEFAULT 0,
    total_customers INT DEFAULT 0,
    total_revenue DECIMAL(15, 2) DEFAULT 0,
    total_cost DECIMAL(15, 2) DEFAULT 0,
    gross_profit DECIMAL(15, 2) DEFAULT 0,
    average_order_value DECIMAL(12, 2) DEFAULT 0,
    conversion_rate DECIMAL(5, 2) DEFAULT 0,
    cart_abandonment_rate DECIMAL(5, 2) DEFAULT 0,
    inventory_turnover DECIMAL(10, 2) DEFAULT 0,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ecom_date FOREIGN KEY (date_id) REFERENCES public.dim_dates(date_id)
);

-- Supply Chain Analytics Mart
CREATE TABLE IF NOT EXISTS analytics.supply_chain_daily_metrics (
    date_id INT PRIMARY KEY,
    total_deliveries INT DEFAULT 0,
    on_time_deliveries INT DEFAULT 0,
    on_time_delivery_pct DECIMAL(5, 2) DEFAULT 0,
    total_procurement_cost DECIMAL(15, 2) DEFAULT 0,
    average_lead_time_days DECIMAL(10, 2) DEFAULT 0,
    supplier_quality_score DECIMAL(5, 2) DEFAULT 0,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sc_date FOREIGN KEY (date_id) REFERENCES public.dim_dates(date_id)
);

-- Financial Analytics Mart
CREATE TABLE IF NOT EXISTS analytics.financial_daily_metrics (
    date_id INT PRIMARY KEY,
    total_revenue DECIMAL(15, 2) DEFAULT 0,
    total_expense DECIMAL(15, 2) DEFAULT 0,
    net_income DECIMAL(15, 2) DEFAULT 0,
    budget_variance DECIMAL(15, 2) DEFAULT 0,
    cash_position DECIMAL(15, 2) DEFAULT 0,
    gross_margin_pct DECIMAL(5, 2) DEFAULT 0,
    operating_margin_pct DECIMAL(5, 2) DEFAULT 0,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_fin_date FOREIGN KEY (date_id) REFERENCES public.dim_dates(date_id)
);

-- Unified KPI Mart
CREATE TABLE IF NOT EXISTS analytics.unified_kpi_metrics (
    date_id INT PRIMARY KEY,
    revenue_per_supplier DECIMAL(15, 2) DEFAULT 0,
    profit_per_product DECIMAL(15, 2) DEFAULT 0,
    order_to_cash_cycle_days INT DEFAULT 0,
    inventory_to_sales_ratio DECIMAL(10, 2) DEFAULT 0,
    cash_conversion_cycle_days INT DEFAULT 0,
    dw_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_kpi_date FOREIGN KEY (date_id) REFERENCES public.dim_dates(date_id)
);

-- ============================================================================
-- STAGING TABLES (for CDC and temporary data)
-- ============================================================================

CREATE TABLE IF NOT EXISTS staging.stg_orders (
    order_id BIGINT PRIMARY KEY,
    customer_id BIGINT,
    product_id BIGINT,
    supplier_id BIGINT,
    order_date TIMESTAMP,
    quantity INT,
    amount DECIMAL(12, 2),
    status VARCHAR(50),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS staging.stg_deliveries (
    delivery_id BIGINT PRIMARY KEY,
    supplier_id BIGINT,
    product_id BIGINT,
    po_id BIGINT,
    quantity_ordered INT,
    quantity_delivered INT,
    delivery_date TIMESTAMP,
    promised_date TIMESTAMP,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS staging.stg_transactions (
    transaction_id BIGINT PRIMARY KEY,
    gl_account_id VARCHAR(20),
    amount DECIMAL(15, 2),
    transaction_date TIMESTAMP,
    description VARCHAR(500),
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- ============================================================================
-- DATA QUALITY & AUDIT TABLES
-- ============================================================================

CREATE TABLE IF NOT EXISTS public.data_quality_log (
    check_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    check_name VARCHAR(255),
    table_name VARCHAR(255),
    status VARCHAR(50),  -- PASSED, FAILED, WARNING
    record_count BIGINT,
    failed_count BIGINT,
    error_message TEXT,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.dw_load_audit (
    load_id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    process_name VARCHAR(255),
    source_system VARCHAR(100),
    table_name VARCHAR(255),
    record_count BIGINT,
    status VARCHAR(50),  -- SUCCESS, FAILED, PARTIAL
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    error_message TEXT
);

-- Create indexes for performance
CREATE INDEX idx_dq_log_timestamp ON public.data_quality_log(run_timestamp);
CREATE INDEX idx_load_audit_timestamp ON public.dw_load_audit(end_time);
