-- ─────────────────────────────────────────────
-- RPR Automated — PostgreSQL Schema
-- Run via setup_mac.sh or manually:
--   psql -U rpr_user -d rpr_automated -f database/schema.sql
-- ─────────────────────────────────────────────

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ══════════════════════════════════════════════
-- PRODUCTS & SKUs
-- ══════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku             VARCHAR(100) UNIQUE NOT NULL,
    title           VARCHAR(500) NOT NULL,
    category        VARCHAR(100),
    amazon_asin     VARCHAR(20),
    ebay_item_id    VARCHAR(50),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- INVENTORY — WAREHOUSE
-- ══════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS inventory_warehouse (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku             VARCHAR(100) NOT NULL REFERENCES products(sku),
    quantity        INTEGER NOT NULL DEFAULT 0,
    location        VARCHAR(100),           -- optional bin/shelf location
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- INVENTORY — FBA
-- ══════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS inventory_fba (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku             VARCHAR(100) NOT NULL REFERENCES products(sku),
    qty_in_transit  INTEGER NOT NULL DEFAULT 0,   -- sent to Amazon, not confirmed
    qty_available   INTEGER NOT NULL DEFAULT 0,   -- confirmed at Amazon FC
    qty_reserved    INTEGER NOT NULL DEFAULT 0,   -- reserved for pending orders
    shipment_id     VARCHAR(100),                 -- Amazon FBA shipment reference
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- SHIPMENTS — LOT COST LAYERS (FIFO)
-- Each row = one lot / shipment received from Ryan's CSV
-- ══════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS shipment_lots (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku             VARCHAR(100) NOT NULL REFERENCES products(sku),
    shipment_ref    VARCHAR(100),               -- e.g. "LOT-2024-04-01-A"
    received_date   DATE NOT NULL,
    quantity_total  INTEGER NOT NULL,           -- units in this lot
    quantity_remaining INTEGER NOT NULL,        -- units not yet consumed by FIFO
    unit_cost       NUMERIC(10,4) NOT NULL,     -- acquisition cost per unit
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- SALES — AMAZON
-- ══════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sales_amazon (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id            VARCHAR(100) UNIQUE NOT NULL,
    sku                 VARCHAR(100) NOT NULL REFERENCES products(sku),
    asin                VARCHAR(20),
    fulfillment_type    VARCHAR(10) NOT NULL CHECK (fulfillment_type IN ('FBA','FBM')),
    sale_price          NUMERIC(10,2) NOT NULL,
    quantity            INTEGER NOT NULL DEFAULT 1,
    referral_fee        NUMERIC(10,2),
    fba_fulfillment_fee NUMERIC(10,2),          -- 0 for FBM
    other_fees          NUMERIC(10,2) DEFAULT 0,
    -- FIFO cost assigned at sale time
    unit_cost_fifo      NUMERIC(10,4),
    lot_id              UUID REFERENCES shipment_lots(id),
    -- calculated fields
    net_profit          NUMERIC(10,2),
    margin_pct          NUMERIC(6,2),
    sale_date           TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- SALES — EBAY
-- ══════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sales_ebay (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id            VARCHAR(100) UNIQUE NOT NULL,
    sku                 VARCHAR(100) NOT NULL REFERENCES products(sku),
    ebay_item_id        VARCHAR(50),
    sale_price          NUMERIC(10,2) NOT NULL,
    quantity            INTEGER NOT NULL DEFAULT 1,
    final_value_fee     NUMERIC(10,2),
    shipping_cost       NUMERIC(10,2) DEFAULT 0,
    other_fees          NUMERIC(10,2) DEFAULT 0,
    -- FIFO cost assigned at sale time
    unit_cost_fifo      NUMERIC(10,4),
    lot_id              UUID REFERENCES shipment_lots(id),
    -- calculated fields
    net_profit          NUMERIC(10,2),
    margin_pct          NUMERIC(6,2),
    sale_date           TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- FBA SHIPMENT LOG
-- Tracks shipments sent to Amazon FBA
-- ══════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS fba_shipments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shipment_id     VARCHAR(100) UNIQUE NOT NULL,   -- Amazon FBA shipment ID
    sku             VARCHAR(100) NOT NULL REFERENCES products(sku),
    quantity_sent   INTEGER NOT NULL,
    status          VARCHAR(50),            -- WORKING, SHIPPED, IN_TRANSIT, RECEIVING, CLOSED
    ship_date       DATE,
    confirmed_date  DATE,                   -- NULL until Amazon confirms receipt
    days_in_transit INTEGER,               -- computed
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- ALERTS LOG
-- Record of every alert fired (for audit + dedup)
-- ══════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS alerts_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_type      VARCHAR(100) NOT NULL,  -- LOW_STOCK, CRITICAL_STOCK, FBA_DELAY, etc.
    sku             VARCHAR(100) REFERENCES products(sku),
    message         TEXT NOT NULL,
    sent_at         TIMESTAMPTZ DEFAULT NOW(),
    email_sent      BOOLEAN DEFAULT FALSE
);

-- ══════════════════════════════════════════════
-- SYNC LOG
-- Tracks every API sync run for debugging
-- ══════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS sync_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel         VARCHAR(20) NOT NULL CHECK (channel IN ('amazon','ebay','csv')),
    status          VARCHAR(20) NOT NULL CHECK (status IN ('success','error','partial')),
    records_synced  INTEGER DEFAULT 0,
    error_message   TEXT,
    synced_at       TIMESTAMPTZ DEFAULT NOW()
);

-- ══════════════════════════════════════════════
-- INDEXES — for dashboard query performance
-- ══════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_sales_amazon_sku       ON sales_amazon(sku);
CREATE INDEX IF NOT EXISTS idx_sales_amazon_date      ON sales_amazon(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_ebay_sku         ON sales_ebay(sku);
CREATE INDEX IF NOT EXISTS idx_sales_ebay_date        ON sales_ebay(sale_date);
CREATE INDEX IF NOT EXISTS idx_shipment_lots_sku      ON shipment_lots(sku);
CREATE INDEX IF NOT EXISTS idx_inventory_wh_sku       ON inventory_warehouse(sku);
CREATE INDEX IF NOT EXISTS idx_inventory_fba_sku      ON inventory_fba(sku);
CREATE INDEX IF NOT EXISTS idx_fba_shipments_status   ON fba_shipments(status);

-- ══════════════════════════════════════════════
-- UPDATED_AT trigger function
-- ══════════════════════════════════════════════

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER trg_fba_shipments_updated_at
    BEFORE UPDATE ON fba_shipments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE OR REPLACE TRIGGER trg_inventory_fba_updated_at
    BEFORE UPDATE ON inventory_fba
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
