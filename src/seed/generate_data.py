import psycopg2
from datetime import datetime, timedelta
import random
import time

def seed_data():
    conn_params = {
        "host": "localhost",
        "database": "ecommerce_db",
        "user": "admin",
        "password": "password123",
        "port": 5432
    }

    print("Connecting to PostgreSQL...")
    # Wait for postgres to be ready if running for the first time
    retries = 5
    conn = None
    while retries > 0:
        try:
            conn = psycopg2.connect(**conn_params)
            break
        except Exception as e:
            print(f"Waiting for Postgres... {e}")
            time.sleep(5)
            retries -= 1
    
    if not conn:
        print("Could not connect to PostgreSQL")
        return

    cur = conn.cursor()

    # Create Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            customer_id INT,
            order_amount DECIMAL(10, 2),
            status VARCHAR(20),
            created_at TIMESTAMP
        );
    """)

    # Generate Data
    statuses = ['COMPLETED', 'PENDING', 'CANCELLED', 'SHIPPED']
    data = []
    
    # Generate 1000 records across 8 years (2018 to 2026)
    start_date = datetime(2018, 1, 1)
    
    print("Generating seed data...")
    for i in range(1000):
        # Random date between 2018 and now
        random_days = random.randint(0, (datetime.now() - start_date).days)
        created_at = start_date + timedelta(days=random_days)
        
        customer_id = random.randint(100, 999)
        amount = round(random.uniform(10.0, 500.0), 2)
        status = random.choice(statuses)
        
        data.append((customer_id, amount, status, created_at))

    # Insert Data
    insert_query = "INSERT INTO orders (customer_id, order_amount, status, created_at) VALUES (%s, %s, %s, %s)"
    cur.executemany(insert_query, data)

    conn.commit()
    print(f"Successfully seeded {len(data)} records into 'orders' table.")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    seed_data()
