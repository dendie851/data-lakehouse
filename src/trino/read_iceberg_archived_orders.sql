-- ============================================================
-- Trino Query: Read Parquet files dari Iceberg Metadata
-- ============================================================
-- Tabel: db_ecommerce.archived_orders
-- Metadata Location: s3a://warehouse/db_ecommerce/archived_orders/metadata/
-- Data Location: s3a://warehouse/db_ecommerce/archived_orders/data/
-- ============================================================

-- 1. List semua schemas/databases yang tersedia di Iceberg catalog
SHOW SCHEMAS FROM iceberg;

-- 2. List semua tabel di database db_ecommerce
SHOW TABLES FROM iceberg.db_ecommerce;

-- 3. Deskripsi struktur tabel archived_orders
DESCRIBE iceberg.db_ecommerce.archived_orders;

-- 4. Baca seluruh data dari tabel archived_orders (Parquet files via Iceberg metadata)
SELECT *
FROM iceberg.db_ecommerce.archived_orders
LIMIT 100;

-- 5. Hitung jumlah total record yang sudah di-arsip
SELECT COUNT(*) AS total_archived_orders
FROM iceberg.db_ecommerce.archived_orders;

-- 6. Analisis data: Jumlah order per status
SELECT
    order_status,
    COUNT(*)        AS total_orders,
    SUM(total_amount) AS total_revenue
FROM iceberg.db_ecommerce.archived_orders
GROUP BY order_status
ORDER BY total_orders DESC;

-- 7. Analisis data: Revenue per bulan/tahun
SELECT
    DATE_FORMAT(created_at, '%Y-%m') AS order_month,
    COUNT(*)                         AS total_orders,
    SUM(total_amount)                AS total_revenue,
    AVG(total_amount)                AS avg_order_value
FROM iceberg.db_ecommerce.archived_orders
GROUP BY DATE_FORMAT(created_at, '%Y-%m')
ORDER BY order_month;

-- 8. Lihat snapshot metadata Iceberg (versioning info)
SELECT
    committed_at,
    operation,
    manifest_count,
    added_data_files_count,
    added_rows_count,
    deleted_data_files_count,
    deleted_rows_count
FROM iceberg.db_ecommerce.archived_orders$snapshots;

-- 9. Lihat metadata files Iceberg (manifest list)
SELECT *
FROM iceberg.db_ecommerce.archived_orders$files;

-- 10. Lihat history operasi Iceberg (audit trail)
SELECT
    made_current_at,
    snapshot_id,
    operation,
    ins,
    del
FROM iceberg.db_ecommerce.archived_orders$history;

-- 11. Partitions info
SELECT *
FROM iceberg.db_ecommerce.archived_orders$partitions;

-- 12. Query untuk melihat schema evolution (jika ada perubahan kolom)
SELECT *
FROM iceberg.db_ecommerce.archived_orders$snapshots
ORDER BY committed_at DESC;