# Bongdaplus News Crawler

Dự án crawl dữ liệu tin tức bóng đá từ trang [Bongdaplus.vn](https://bongdaplus.vn), xử lý dữ liệu theo schema database, và lưu trữ vào PostgreSQL hoặc xuất file CSV.

## Yêu cầu hệ thống

- Python 3.8+
- PostgreSQL
- pip hoặc conda

## Cài đặt

### 1. Cài đặt các package phụ thuộc

```bash
pip install -r requirements.txt
```

### 2. Cấu hình Database (tùy chọn)

Tạo file `.env` trong thư mục gốc dự án:

```
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_db_name
```

Thay thế các giá trị phù hợp với cấu hình PostgreSQL của bạn.

## Cách sử dụng

### 1. Crawl dữ liệu từ Bongdaplus

Lệnh cơ bản:

```bash
python crawl_data/script.py
```

Kết quả sẽ được lưu vào `bongdaplus_crawled.json` trong thư mục gốc.

**Các tùy chọn:**

```bash
# Crawl 20 bài mà không lấy chi tiết từng bài
python crawl_data/script.py --max-items 20 --no-details

# Crawl từ section khác
python crawl_data/script.py --section-url https://bongdaplus.vn/bong-da-viet-nam

# Crawl và in kết quả ra màn hình thay vì lưu file
python crawl_data/script.py --stdout

# Giới hạn số trang "Xem thêm" (mặc định là 1)
python crawl_data/script.py --max-viewmore-pages 2

# Thêm độ trễ giữa các request (tính bằng giây)
python crawl_data/script.py --delay 1.0
```

### 2. Xuất dữ liệu ra CSV

```bash
python check_by_csv.py
```

Kết quả: `bongdaplus.csv` với cột:
- id
- title
- url
- published_time (định dạng: YYYY-MM-DD HH:MM:SS)
- author
- tag (breadcrumbs nối bằng dấu phẩy)
- content
- fetched_at (theo múi giờ Vietnam UTC+7)

**Tùy chọn:**

```bash
# Chỉ định đường dẫn JSON input
python check_by_csv.py --json-path /path/to/file.json

# Bắt đầu ID từ số khác (mặc định là 1)
python check_by_csv.py --start-id 100
```

### 3. Lưu dữ liệu vào PostgreSQL

```bash
python utils/save_to_db.py
```

Điều kiện:
- File `.env` phải được cấu hình đúng
- PostgreSQL server phải đang chạy
- Database phải tồn tại (script sẽ tạo table nếu chưa có)

**Tùy chọn:**

```bash
# Chỉ preview dữ liệu sẽ được insert, không thực hiện insert
python utils/save_to_db.py --dry-run

# Chỉ định đường dẫn JSON input
python utils/save_to_db.py --json-path /path/to/file.json

# Chỉ định database URL trực tiếp (bỏ qua .env)
python utils/save_to_db.py --database-url postgresql+psycopg2://user:pass@localhost:5432/dbname
```

## Cấu trúc dữ liệu

### JSON Output (bongdaplus_crawled.json)

```json
{
  "source_url": "https://bongdaplus.vn/bong-da-viet-nam",
  "section_title": "Bóng đá Việt Nam",
  "fetched_at": "2024-04-04T10:30:45.123456+00:00",
  "item_count": 35,
  "items": [
    {
      "title": "Tiêu đề bài viết",
      "url": "https://bongdaplus.vn/...",
      "author": "Tên tác giả",
      "published_time": "2 giờ trước",
      "description": "Mô tả ngắn bài viết",
      "breadcrumbs": ["Bóng đá", "Tin tức", "Việt Nam"],
      "content": "Nội dung đầy đủ của bài viết..."
    }
  ]
}
```

### Database Schema

Table `soccer_news`:

| Cột | Kiểu | Ghi chú |
|-----|------|--------|
| id | INTEGER | Primary key, auto increment |
| title | TEXT | NOT NULL |
| url | TEXT | UNIQUE, NOT NULL |
| published_time | TIMESTAMP | Múi giờ UTC+7 |
| author | TEXT | Cho phép NULL |
| tag | TEXT | Breadcrumbs nối bằng ", " |
| content | TEXT | Cho phép NULL |
| fetched_at | TIMESTAMP | Múi giờ UTC+7 |

## Quy trình xử lý dữ liệu

1. **Crawling** (`crawl_data/script.py`):
   - Lấy danh sách bài từ section page
   - Tải thêm bài từ "Xem thêm" pagination
   - Lấy chi tiết từng bài (tác giả, nội dung, breadcrumbs, v.v.)

2. **Transformation** (`utils/handle_json.py`):
   - Chuyển đổi timestamp: "2 giờ trước" → cộng/trừ với fetched_at
   - Chuyển đổi absolute timestamp: "10:30 ngày 03/04/2024" → YYYY-MM-DD HH:MM:SS
   - Chuyển múi giờ UTC+0 → UTC+7 (Việt Nam)
   - Nối breadcrumbs thành tag: ["A", "B", "C"] → "A, B, C"

3. **Persistence**:
   - **CSV** (`check_by_csv.py`): Export ra file .csv
   - **PostgreSQL** (`utils/save_to_db.py`): Upsert vào database (unique trên url)

## Troubleshooting

### Lỗi: "ModuleNotFoundError: No module named '...'"

→ Chạy `pip install -r requirements.txt`

### Lỗi: "Connection refused" hoặc PostgreSQL error

→ Kiểm tra:
- PostgreSQL server đang chạy
- File `.env` cấu hình đúng (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME)
- Database tồn tại

### Crawler chậm/timeout

→ Sử dụng `--delay` để giảm số request:
```bash
python crawl_data/script.py --delay 1.0 --max-items 10
```

### Dữ liệu thiếu (author, content, v.v.)

→ Đảm bảo không sử dụng `--no-details`. Script mặc định sẽ crawl chi tiết từng bài.

Chạy ví dụ:

```bash
python check_by_csv.py --json-path bongdaplus_crawl.json --csv-path bongdaplus_news.csv
```

Tuỳ chọn id bắt đầu:

```bash
python check_by_csv.py --start-id 1
```
