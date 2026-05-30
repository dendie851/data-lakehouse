from pyspark.sql import SparkSession
from pyspark.sql.functions import col, add_months, current_date
import datetime

def run_etl():
    # Initialize Spark Session
    # Config is mostly picked up from spark-defaults.conf when using spark-submit,
    # but we can set explicit app name here.
    spark = SparkSession.builder \
        .appName("PostgresToIcebergArchive") \
        .getOrCreate()

    print("Spark Session Initialized.")

    # 1. Read from PostgreSQL
    jdbc_url = "jdbc:postgresql://postgres:5432/ecommerce_db"
    connection_properties = {
        "user": "admin",
        "password": "password123",
        "driver": "org.postgresql.Driver"
    }

    print("Reading data from PostgreSQL...")
    df = spark.read.jdbc(url=jdbc_url, table="orders", properties=connection_properties)
    
    # 2. Identify data older than 5 years
    # 5 years = 60 months
    five_years_ago = datetime.datetime.now() - datetime.timedelta(days=5*365)
    print(f"Archiving data created before: {five_years_ago}")

    archive_df = df.filter(col("created_at") < five_years_ago)
    
    count = archive_df.count()
    print(f"Found {count} records to archive.")

    if count > 0:
        # 3. Write to Apache Iceberg
        # We use the 'local' catalog defined in spark-defaults.conf
        # Table name format: catalog.db.table
        
        # Ensure database exists in Iceberg
        spark.sql("CREATE DATABASE IF NOT EXISTS local.db_ecommerce")

        print("Writing data to Apache Iceberg (MinIO)...")
        archive_df.writeTo("local.db_ecommerce.archived_orders") \
            .tableProperty("format-version", "2") \
            .createOrReplace()

        print("Archive successful.")
        
        # 4. Optional: Verification
        spark.sql("SELECT count(*) as total_archived FROM local.db_ecommerce.archived_orders").show()
    else:
        print("No data to archive.")

    spark.stop()

if __name__ == "__main__":
    run_etl()
