import sqlite3
from pathlib import Path

# Database file
DB_FILE = Path(__file__).parent / "deposit_rates.db"


def init_db_with_dummy_data():
    # todo: make in cents instead of euros
    DUMMY_DATA = [
        # 0-29 days
        (0, 100000, 0, 29, 16.0, 16.4),
        (100001, 500000, 0, 29, 16.2, 16.4),
        (500001, 5000000, 0, 29, 16.4, 16.8),
        (5000001, 100000000, 0, 29, 16.6, 16.9),

        # 30-180 days
        (0, 100000, 30, 180, 15.0, 15.4),
        (100001, 500000, 30, 180, 15.2, 15.4),
        (500001, 5000000, 30, 180, 15.4, 15.8),
        (5000001, 100000000, 30, 180, 15.6, 15.9),

        # 182-365 days
        (0, 100000, 181, 365, 14.0, 14.4),
        (100001, 500000, 181, 365, 14.2, 14.4),
        (500001, 5000000, 181, 365, 14.4, 14.8),
        (5000001, 100000000, 181, 365, 14.6, 14.9),
    ]

    # Create a connection to SQLite database
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create the deposit_rates table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS deposit_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        min_amount INTEGER NOT NULL,
        max_amount INTEGER NOT NULL,
        min_duration INTEGER NOT NULL,
        max_duration INTEGER NOT NULL,
        min_rate DECIMAL(5,2) NOT NULL,
        max_rate DECIMAL(5,2) NOT NULL
    );
    """)

    # Create an index for faster range queries
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_deposit_search 
    ON deposit_rates (min_amount, max_amount, min_duration, max_duration);
    """)

    # Insert dummy data
    cursor.executemany("""
    INSERT INTO deposit_rates (min_amount, max_amount, min_duration, max_duration, min_rate, max_rate) 
    VALUES (?, ?, ?, ?, ?, ?);
    """, DUMMY_DATA)

    # Commit changes and close connection
    conn.commit()
    conn.close()


def get_deposit_rates_range(amount, duration):
    deposit_rates_db_conn = sqlite3.connect(DB_FILE)
    cursor = deposit_rates_db_conn.cursor()
    cursor.execute("""
    SELECT MIN(min_rate) AS min_rate, MAX(max_rate) AS max_rate
    FROM deposit_rates
    WHERE min_amount <= ? AND max_amount >= ?
    AND min_duration <= ? AND max_duration >= ?;
    """, (amount, amount, duration, duration))

    min_rate, max_rate = cursor.fetchone()
    deposit_rates_db_conn.close()
    return min_rate, max_rate


if __name__ == '__main__':
    init_db_with_dummy_data()

    min_r, max_r = get_deposit_rates_range(350000, 30)
    print(f'Deposit rates: {min_r}%, {max_r}%')
