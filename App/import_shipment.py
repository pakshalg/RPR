# ─────────────────────────────────────────────
# RPR Automated — Inbound Shipment CSV Importer
# Run from App/ directory:
#   python import_shipment.py path/to/file.csv
# ─────────────────────────────────────────────

import sys
import csv
from decimal import Decimal
from datetime import datetime
from database import get_connection, release_connection


def parse_cost(value: str) -> Decimal:
    return Decimal(value.replace("$", "").replace(",", "").strip())


def parse_date(value: str) -> str:
    return datetime.strptime(value.strip(), "%m/%d/%Y").date().isoformat()


def import_csv(filepath: str):
    with open(filepath, newline="") as f:
        # Skip leading empty rows, find the header row
        lines = f.readlines()
        header_idx = next(i for i, l in enumerate(lines) if "shipment_id" in l)
        reader = csv.DictReader(lines[header_idx:])
        rows = [row for row in reader if row.get("sku", "").strip()]

    if not rows:
        print("No data rows found.")
        return

    conn = get_connection()
    cur = conn.cursor()

    products_seen = set()
    inserted_lots = 0

    for row in rows:
        sku             = row["sku"].strip()
        product_name    = row["product_name"].strip()
        category        = row["category"].strip()
        asin            = row["asin"].strip()
        ebay_item_id    = row["ebay_item_id"].strip()
        shipment_id     = row["shipment_id"].strip()
        shipment_date   = parse_date(row["shipment_date"])
        quantity        = int(row["quantity_received"].strip())
        unit_cost       = parse_cost(row["unit_cost"])
        supplier        = row["supplier_name"].strip()
        notes           = f"Supplier: {supplier}" + (f" | {row['notes'].strip()}" if row.get("notes", "").strip() else "")

        # Upsert product (once per unique SKU)
        if sku not in products_seen:
            cur.execute("""
                INSERT INTO products (sku, title, category, amazon_asin, ebay_item_id)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (sku) DO UPDATE SET
                    title        = EXCLUDED.title,
                    category     = EXCLUDED.category,
                    amazon_asin  = EXCLUDED.amazon_asin,
                    ebay_item_id = EXCLUDED.ebay_item_id,
                    updated_at   = NOW()
            """, (sku, product_name, category, asin, ebay_item_id))
            products_seen.add(sku)
            print(f"  ✓ Product upserted: {sku} — {product_name}")

        # Insert shipment lot (FIFO cost layer)
        cur.execute("""
            INSERT INTO shipment_lots
                (sku, shipment_ref, received_date, quantity_total, quantity_remaining, unit_cost, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (sku, shipment_id, shipment_date, quantity, quantity, unit_cost, notes))
        inserted_lots += 1

        # Upsert warehouse inventory (add quantity)
        cur.execute("""
            INSERT INTO inventory_warehouse (sku, quantity)
            VALUES (%s, %s)
            ON CONFLICT (sku) DO UPDATE SET
                quantity   = inventory_warehouse.quantity + EXCLUDED.quantity,
                updated_at = NOW()
        """, (sku, quantity))

    conn.commit()
    cur.close()
    release_connection(conn)

    print(f"\nDone. {len(products_seen)} products, {inserted_lots} shipment lots imported.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python import_shipment.py path/to/file.csv")
        sys.exit(1)
    import_csv(sys.argv[1])
