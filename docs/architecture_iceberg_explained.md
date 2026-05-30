# Arsitektur Apache Iceberg di Data Lakehouse ini

## Jawaban: Apache Iceberg TIDAK memerlukan container tersendiri

**Apache Iceberg bukan service/container** - Iceberg adalah **library/format file** yang dijalankan **di dalam** container lain (Spark dan Trino).

---

## Diagram Arsitektur

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CONTAINER LAYOUT                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   POSTGRES   │    │    MINIO     │    │       SPARK          │  │
│  │  (Container) │    │  (Container) │    │     (Container)      │  │
│  │              │    │              │    │                      │  │
│  │  📦 Iceberg  │    │  📁 Parquet  │    │  ⚙️ Iceberg Library  │  │
│  │  JDBC Catalog│    │  Data Files  │    │  (JAR dependency)    │  │
│  │  Metadata    │    │  + Metadata  │    │                      │  │
│  └──────┬───────┘    └──────┬───────┘    └──────────┬───────────┘  │
│         │                   │                       │               │
│         └───────────────────┼───────────────────────┘               │
│                             │                                       │
│                    ┌────────┴────────┐                              │
│                    │  TRINO (Container) │                           │
│                    │  ⚙️ Iceberg Library │                           │
│                    │  (Connector)       │                           │
│                    └───────────────────┘                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Dimana Iceberg Digunakan?

### 1. Container: **Spark** (`spark-master` + `spark-worker`)

**File:** `config/spark/spark-defaults.conf`

```
spark.jars.packages  org.apache.iceberg:iceberg-spark-runtime-3.4_2.12:1.3.1
```

| Config | Penjelasan |
|--------|-----------|
| `spark.sql.extensions` | Iceberg extensions untuk Spark SQL |
| `spark.sql.catalog.local` | Register Iceberg catalog bernama "local" |
| `spark.sql.catalog.local.catalog-impl` | Iceberg JDBC catalog implementation |
| `spark.sql.catalog.local.uri` | PostgreSQL JDBC URL untuk metadata |
| `spark.sql.catalog.local.warehouse` | `s3a://warehouse/` = lokasi Parquet files di MinIO |

**Proses:** Spark ETL (`src/etl/archive_to_iceberg.py`) menggunakan Iceberg untuk:
- Membaca data dari PostgreSQL (OLTP)
- Menulis ke format Iceberg (Parquet + metadata JSON)
- Menyimpan ke MinIO via S3A

```python
# Iceberg digunakan di sini:
spark.sql("CREATE DATABASE IF NOT EXISTS local.db_ecommerce")   # Iceberg catalog
archive_df.writeTo("local.db_ecommerce.archived_orders")        # Iceberg write
    .tableProperty("format-version", "2")                       # Iceberg format v2
    .createOrReplace()
```

---

### 2. Container: **Trino** (`trino_engine`)

**File:** `config/trino/catalog/iceberg.properties`

```properties
connector.name=iceberg                              # ← Iceberg connector
iceberg.catalog.type=JDBC                           # ← JDBC catalog (sama dgn Spark)
iceberg.jdbc-catalog.connection-url=jdbc:postgresql://postgres:5432/ecommerce_db
iceberg.jdbc-catalog.default-warehouse-dir=s3a://warehouse/
```

**Proses:** Trino menggunakan Iceberg connector untuk:
- Membaca metadata dari PostgreSQL (catalog yang sama dengan Spark)
- Membaca file Parquet dari MinIO
- Menjalankan SQL queries atas data Parquet

---

### 3. Container: **PostgreSQL** (`postgres_oltp`)

**Peran:** Menyimpan **Iceberg JDBC Catalog metadata** di database `ecommerce_db`:
- Informasi lokasi setiap table
- Snapshot history
- Manifest file locations
- Schema evolution records

**Tidak ada Iceberg library di container ini** - PostgreSQL hanya menyimpan metadata sebagai tabel biasa.

---

### 4. Container: **MinIO** (`minio_storage`)

**Peran:** Menyimpan **file fisik Iceberg** di bucket `warehouse`:

```
s3a://warehouse/
└── db_ecommerce/
    └── archived_orders/
        ├── metadata/
        │   ├── 00001-d8368cc6-*.metadata.json   ← Iceberg metadata
        │   └── *.manifest                        ← Manifest files
        └── data/
            └── *.parquet                          ← Data Parquet files
```

**Tidak ada Iceberg library di container ini** - MinIO hanya menyimpan file sebagai object storage.

---

## Ringkasan: Container mana yang pakai Iceberg?

| Container | Pakai Iceberg? | Sebagai Apa? | File Config |
|-----------|---------------|--------------|-------------|
| **Spark** | ✅ Ya | Library (JAR) untuk menulis Iceberg tables | `spark-defaults.conf` |
| **Trino** | ✅ Ya | Connector untuk membaca Iceberg tables | `iceberg.properties` |
| **PostgreSQL** | ❌ Tidak | Hanya menyimpan catalog metadata sebagai tabel DB | - |
| **MinIO** | ❌ Tidak | Hanya menyimpan file Parquet & metadata JSON | - |
| **Metabase** | ❌ Tidak | Visualization layer via Trino | - |

---

## Kesimpulan

```
Apache Iceberg = Library/Format (bukan container)

Digunakan di:
├── Spark    → sebagai JAR dependency  → WRITE data ke Iceberg format
├── Trino    → sebagai Connector       → READ data dari Iceberg format
├── Postgres → sebagai JDBC Catalog    → STORE metadata (bukan Iceberg library)
└── MinIO    → sebagai Data Lake       → STORE Parquet + metadata files (bukan Iceberg library)
```

**Tidak perlu menambahkan container Iceberg baru.** Arsitektur saat ini sudah benar:
- Iceberg berjalan sebagai **library di dalam Spark** (untuk ETL/write)
- Iceberg berjalan sebagai **connector di dalam Trino** (untuk query/read)
- Metadata disimpan di **PostgreSQL** (shared JDBC catalog)
- Data files disimpan di **MinIO** (S3A-compatible object storage)