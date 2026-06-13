import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")


def build_cloud_tables():
    print("🔄 Connecting to Render to build database schema...")

    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    schema_sql = """
    CREATE TABLE IF NOT EXISTS clients (
        client_id SERIAL PRIMARY KEY,
        phone_number VARCHAR(30) UNIQUE NOT NULL,
        full_name VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS bookings (
        booking_id SERIAL PRIMARY KEY,
        phone_number VARCHAR(30) REFERENCES clients(phone_number),
        booking_date DATE NOT NULL,
        booking_time TIME NOT NULL,
        service_type VARCHAR(50) DEFAULT 'Haircut',
        status VARCHAR(20) DEFAULT 'Confirmed',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_slot UNIQUE (booking_date, booking_time)
    );

    CREATE TABLE IF NOT EXISTS financial_ledger (
        transaction_id SERIAL PRIMARY KEY,
        date DATE NOT NULL,
        category VARCHAR(20) NOT NULL,
        description VARCHAR(255),
        amount DECIMAL(10,2) NOT NULL,
        payment_method VARCHAR(20) NOT NULL,
        booking_id INT REFERENCES bookings(booking_id),
        reconciled_with_bank BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE OR REPLACE VIEW daily_profitability AS
    SELECT
        date,
        SUM(CASE WHEN category IN ('Service','Retail') THEN amount ELSE 0 END) AS gross_revenue,
        SUM(CASE WHEN category = 'Expense' THEN amount ELSE 0 END) AS total_expenses,
        (
            SUM(CASE WHEN category IN ('Service','Retail') THEN amount ELSE 0 END)
            -
            SUM(CASE WHEN category = 'Expense' THEN amount ELSE 0 END)
        ) AS net_profit
    FROM financial_ledger
    GROUP BY date;

    ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS last_service VARCHAR(50);

    ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS last_visit_date DATE;

    ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS total_bookings INTEGER DEFAULT 0;

    ALTER TABLE clients
    ADD COLUMN IF NOT EXISTS notes TEXT;

    CREATE TABLE IF NOT EXISTS conversation_state (
        phone_number VARCHAR(30) PRIMARY KEY,
        full_name VARCHAR(100),
        service_type VARCHAR(50),
        booking_date DATE,
        booking_time TIME,
        awaiting_confirmation BOOLEAN DEFAULT FALSE,
        step VARCHAR(50),
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    ALTER TABLE conversation_state
    ADD COLUMN IF NOT EXISTS step VARCHAR(50);

    ALTER TABLE clients
    ALTER COLUMN phone_number TYPE VARCHAR(30);

    ALTER TABLE bookings
    ALTER COLUMN phone_number TYPE VARCHAR(30);

    ALTER TABLE conversation_state
    ALTER COLUMN phone_number TYPE VARCHAR(30);

    CREATE INDEX IF NOT EXISTS idx_bookings_date
    ON bookings(booking_date);

    CREATE INDEX IF NOT EXISTS idx_bookings_date_time
    ON bookings(booking_date, booking_time);

    CREATE INDEX IF NOT EXISTS idx_clients_phone
    ON clients(phone_number);

    CREATE INDEX IF NOT EXISTS idx_conversation_state_phone
    ON conversation_state(phone_number);
    """

    try:
        cursor.execute(schema_sql)
        conn.commit()
        print("✅ Database tables, CRM fields, and conversation state successfully created on Render!")

    except Exception as e:
        conn.rollback()
        print(f"❌ Table creation failed: {e}")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    build_cloud_tables()