# CanteenFlow Architecture & Design Notes

## Technical Decisions
- **SQL Injection Prevention:** Parameterized SQL queries used across `db.py` and blueprints[cite: 3].
- **Atomic Order Tokens:** Daily token numbers restart at 1 using unique constraint `(order_date, token_number)`[cite: 2, 3].
- **Price Integrity:** `unit_price` stored in `order_items` freezes historical order costs[cite: 2, 3].
