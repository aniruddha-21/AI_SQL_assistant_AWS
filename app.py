"""Local prototype for an AWS-style AI SQL Assistant.

Runs with the Python standard library only:
    python app.py
Then open http://127.0.0.1:8012
"""

from __future__ import annotations

import json
import re
import sqlite3
import threading
import webbrowser
from datetime import date, timedelta
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
DB_PATH = ROOT / "demo_store.db"

SCHEMA_DESCRIPTION = """Database: demo retail analytics
- customers(customer_id, name, city, segment, signup_date)
- products(product_id, name, category, unit_price, stock_quantity)
- orders(order_id, customer_id, order_date, status, total_amount)
- order_items(order_item_id, order_id, product_id, quantity, unit_price)
Relationships: orders.customer_id -> customers.customer_id; order_items.order_id -> orders.order_id; order_items.product_id -> products.product_id.
"""


def initialise_database() -> None:
    if DB_PATH.exists():
        return
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.executescript(
        """
        CREATE TABLE customers (
          customer_id INTEGER PRIMARY KEY, name TEXT, city TEXT, segment TEXT, signup_date TEXT
        );
        CREATE TABLE products (
          product_id INTEGER PRIMARY KEY, name TEXT, category TEXT, unit_price REAL, stock_quantity INTEGER
        );
        CREATE TABLE orders (
          order_id INTEGER PRIMARY KEY, customer_id INTEGER, order_date TEXT, status TEXT, total_amount REAL,
          FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
        );
        CREATE TABLE order_items (
          order_item_id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price REAL,
          FOREIGN KEY(order_id) REFERENCES orders(order_id),
          FOREIGN KEY(product_id) REFERENCES products(product_id)
        );
        """
    )
    customers = [
        (1, "Aarav Shah", "Mumbai", "Enterprise", "2024-01-14"),
        (2, "Diya Kapoor", "Delhi", "SMB", "2024-02-03"),
        (3, "Rohan Mehta", "Bengaluru", "Enterprise", "2024-03-18"),
        (4, "Isha Nair", "Chennai", "SMB", "2024-05-09"),
        (5, "Kabir Singh", "Pune", "Consumer", "2024-06-22"),
        (6, "Anaya Rao", "Bengaluru", "Consumer", "2024-08-01"),
        (7, "Vivaan Das", "Kolkata", "SMB", "2024-09-12"),
        (8, "Mira Joshi", "Mumbai", "Enterprise", "2024-10-27"),
    ]
    products = [
        (1, "CloudDesk Pro", "SaaS", 499.0, 36), (2, "Insight BI", "Analytics", 899.0, 12),
        (3, "SecureSync", "Security", 299.0, 74), (4, "FlowOps", "Automation", 649.0, 28),
        (5, "DataLake Starter", "Data", 1099.0, 7), (6, "Support Plus", "Services", 199.0, 120),
    ]
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?)", customers)
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?)", products)
    base = date(2025, 8, 1)
    order_rows, item_rows = [], []
    item_id = 1
    patterns = [(1, 1, 2), (2, 2, 1), (3, 3, 4), (4, 4, 1), (5, 5, 2), (6, 6, 5), (7, 1, 3), (8, 3, 2)]
    for order_id in range(1, 33):
        customer_id, product_id, quantity = patterns[(order_id - 1) % len(patterns)]
        product = products[product_id - 1]
        order_date = (base + timedelta(days=(order_id * 7) % 420)).isoformat()
        status = "Cancelled" if order_id in {11, 27} else ("Pending" if order_id in {9, 24} else "Completed")
        total = product[3] * quantity
        order_rows.append((order_id, customer_id, order_date, status, total))
        item_rows.append((item_id, order_id, product_id, quantity, product[3]))
        item_id += 1
    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", order_rows)
    cursor.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?)", item_rows)
    connection.commit()
    connection.close()


def normalise_sql(sql: str) -> str:
    sql = sql.strip().rstrip(";")
    if not sql.lower().startswith(("select", "with", "pragma table_info")):
        raise ValueError("Safety policy allows read-only SELECT queries only.")
    if re.search(r"\b(insert|update|delete|drop|alter|create|attach|pragma\s+(?!table_info))\b", sql, re.I):
        raise ValueError("Safety policy blocked a database-changing operation.")
    return sql


def generate_sql(question: str) -> tuple[str, str]:
    text = question.lower().strip()
    if text.startswith(("select", "with")):
        return normalise_sql(question), "Executed your supplied read-only SQL."
    if any(term in text for term in ["revenue", "sales", "total sales"]):
        if any(term in text for term in ["month", "monthly", "trend"]):
            return ("SELECT substr(order_date, 1, 7) AS month, ROUND(SUM(total_amount), 2) AS revenue "
                    "FROM orders WHERE status = 'Completed' GROUP BY month ORDER BY month;", "Calculated completed-order revenue by month.")
        if "city" in text:
            return ("SELECT c.city, ROUND(SUM(o.total_amount), 2) AS revenue, COUNT(o.order_id) AS orders "
                    "FROM orders o JOIN customers c ON c.customer_id = o.customer_id "
                    "WHERE o.status = 'Completed' GROUP BY c.city ORDER BY revenue DESC;", "Joined customers and orders, then grouped completed revenue by city.")
        return ("SELECT ROUND(SUM(total_amount), 2) AS total_revenue, COUNT(order_id) AS completed_orders "
                "FROM orders WHERE status = 'Completed';", "Summed completed-order revenue.")
    if any(term in text for term in ["top product", "best selling", "best-selling", "popular product"]):
        return ("SELECT p.name AS product, p.category, SUM(oi.quantity) AS units_sold, "
                "ROUND(SUM(oi.quantity * oi.unit_price), 2) AS revenue FROM order_items oi "
                "JOIN products p ON p.product_id = oi.product_id JOIN orders o ON o.order_id = oi.order_id "
                "WHERE o.status = 'Completed' GROUP BY p.product_id ORDER BY units_sold DESC LIMIT 5;", "Ranked products by completed-order units sold.")
    if any(term in text for term in ["customer", "client"]) and any(term in text for term in ["top", "highest", "valuable"]):
        return ("SELECT c.name AS customer, c.city, c.segment, ROUND(SUM(o.total_amount), 2) AS lifetime_value "
                "FROM customers c JOIN orders o ON o.customer_id = c.customer_id WHERE o.status = 'Completed' "
                "GROUP BY c.customer_id ORDER BY lifetime_value DESC LIMIT 10;", "Ranked customers using completed-order lifetime value.")
    if any(term in text for term in ["inventory", "stock", "low stock"]):
        return "SELECT name AS product, category, stock_quantity, unit_price FROM products WHERE stock_quantity < 30 ORDER BY stock_quantity;", "Found products below the low-stock threshold of 30 units."
    if any(term in text for term in ["order", "status"]):
        return "SELECT status, COUNT(*) AS orders, ROUND(SUM(total_amount), 2) AS value FROM orders GROUP BY status ORDER BY orders DESC;", "Summarised orders and their value by status."
    if "customer" in text or "list" in text:
        return "SELECT name AS customer, city, segment, signup_date FROM customers ORDER BY signup_date DESC LIMIT 20;", "Listed the most recently signed-up customers."
    return ("SELECT 'Try one of the suggested questions, or write a SELECT query.' AS guidance;",
            "I kept this local prototype deterministic. It recognises common analytics questions and also accepts SELECT SQL directly.")


def run_question(question: str) -> dict:
    sql, explanation = generate_sql(question)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    try:
        rows = [dict(row) for row in connection.execute(sql).fetchall()]
    finally:
        connection.close()
    return {"sql": sql, "explanation": explanation, "rows": rows, "schema": SCHEMA_DESCRIPTION}


class AssistantHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if urlparse(self.path).path == "/api/schema":
            self.respond({"schema": SCHEMA_DESCRIPTION})
            return
        if urlparse(self.path).path in {"/", "/index.html"}:
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/query":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length))
            question = str(body.get("question", "")).strip()
            if not question:
                raise ValueError("Please enter a question.")
            self.respond(run_question(question))
        except (ValueError, sqlite3.Error) as error:
            self.respond({"error": str(error)}, 400)

    def respond(self, data: dict, status: int = 200) -> None:
        payload = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt: str, *args: object) -> None:
        print("[AI SQL Assistant] " + fmt % args)


if __name__ == "__main__":
    initialise_database()
    server = None
    for port in range(8012, 8023):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), AssistantHandler)
            break
        except OSError:
            continue
    if server is None:
        raise RuntimeError("Could not find a free port between 8012 and 8022. Close another local server and try again.")
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"\nAI SQL Assistant is ready at {url}\nYour browser should open automatically. Press Ctrl+C to stop.\n", flush=True)
    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    server.serve_forever()
