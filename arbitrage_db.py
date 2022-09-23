import sqlite3


conn = sqlite3.connect("triangle_arbitrage.db")
cursor = conn.cursor()


def insert(data):
    cursor.execute(
        """
        INSERT INTO triangle_arbitrage 
        (bunch, fee_amount, is_arbitrage_opportunity, profit_amount, profit_percentage, best_depth_prices,
        best_depth_qty, checking_time) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, data
    )
    conn.commit()


def delete(row_id):
    row_id = int(row_id)
    cursor.execute(f"DELETE FROM triangle_arbitrage where id={row_id}")
    conn.commit()


def get_cursor():
    return cursor


def _init_db():
    with open("initialization_db.sql", "r") as f:
        sql = f.read()
    cursor.executescript(sql)
    conn.commit()


def check_db_exists():
    cursor.execute("SELECT name FROM sqlite_master "
                   "WHERE type='table' AND name='expense'")
    table_exists = cursor.fetchall()
    if table_exists:
        return
    _init_db()


# check_db_exists()
