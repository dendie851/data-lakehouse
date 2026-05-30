# Trino Authentication - Metabase Connection

## Status: Tidak Ada Authentication di Trino

Project ini **TIDAK mengkonfigurasi authentication** untuk Trino. 

### Bukti

1. **Docker Compose** (`docker-compose.yaml`) - Trino container tidak mount file config.properties:
   ```yaml
   trino:
     image: trinodb/trino:422
     container_name: trino_engine
     ports:
       - "8081:8080"
     volumes:
       - ./config/trino/catalog:/etc/trino/catalog    # Hanya catalog, TIDAK ada config.properties
   ```

2. **Tidak ada file `config.properties`** di `config/trino/` - hanya ada folder `catalog/`

3. **Default Trino behavior** - Docker image `trinodb/trino:422` menggunakan `AllowAll` access control:
   - **Semua username diterima** tanpa validasi
   - **Password diabaikan** (boleh kosong, boleh apa saja)
   - Tidak ada password file atau LDAP

---

## Konfigurasi Metabase (dari Screenshot)

| Field | Value | Keterangan |
|-------|-------|------------|
| Database type | Starburst (Trino) | Trino JDBC driver |
| Host | `trino` | Docker network name |
| Port | `8080` | Internal Trino port (bukan 8081!) |
| Catalog | `iceberg` | Iceberg catalog dari `iceberg.properties` |
| Schema | *(kosong)* | Optional |
| **Username** | **`admin`** | **Bisa diisi APA SAJA** |
| **Password** | **`••••••••`** | **Bisa diisi APA SAJA** |
| Use SSL | OFF | Tidak ada SSL |

### ⚠️ Penting: Port 8080 vs 8081

- **Port 8080** = Port internal Trino di dalam Docker network → **Digunakan oleh Metabase** (karena Metabase dan Trino di Docker network yang sama)
- **Port 8081** = Port mapping ke host machine → **Digunakan untuk akses dari browser luar**

```
Metabase Container ──(docker network)──► trino:8080  ← Internal
Browser localhost  ──(port mapping)────► localhost:8081 → trino:8080  ← External
```

---

## Cara Mengisi Form di Metabase

Karena tidak ada authentication, isi form seperti ini:

```
Host:       trino
Port:       8080
Catalog:    iceberg
Schema:     (kosong)
Username:   admin          ← atau apa saja: trino, user, dll
Password:   (kosong)       ← atau apa saja
Use SSL:    OFF
```

**Username dan password tidak divalidasi** oleh Trino dalam konfigurasi saat ini.

---

## Jika Ingin Menambahkan Authentication (Optional)

Jika ingin Trino benar-benar memvalidasi username/password:

### 1. Buat file password di Trino

```bash
# Di dalam container Trino, buat file:
/etc/trino/users.properties
```

```properties
# Format: username=hashed_password
admin=$2a$10$...hashed_bcrypt...
```

### 2. Buat config.properties

Buat file `config/trino/config.properties`:
```properties
coordinator=true
node-scheduler.include-coordinator=true
http-server.http.port=8080
discovery.uri=http://trino:8080

# Authentication
http-server.authentication.type=PASSWORD
password-authenticator.name=file
file.auth-file=/etc/trino/users.properties
```

### 3. Update docker-compose.yaml

```yaml
trino:
  image: trinodb/trino:422
  container_name: trino_engine
  ports:
    - "8081:8080"
  volumes:
    - ./config/trino/catalog:/etc/trino/catalog
    - ./config/trino/config.properties:/etc/trino/config.properties   # ← Tambah
    - ./config/trino/users.properties:/etc/trino/users.properties     # ← Tambah
```

**Tapi untuk setup saat ini, authentication TIDAK diperlukan** - Metabase bisa langsung konek ke Trino tanpa validasi credentials.