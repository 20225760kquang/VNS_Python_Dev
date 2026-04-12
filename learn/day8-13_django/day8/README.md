# Django Inventory Management System

Dự án Hệ thống Quản lý Kho Dữ liệu (Inventory System) được viết bằng Django, ứng dụng cấu trúc **MVT (Model-View-Template)**, sử dụng **Django Admin** trực quan và sử dụng **QuerySet API**.

## Tính năng nổi bật
* **Quản trị Admin tối ưu**: Giao diện quản lý nâng cao với Custom Filters, Search và Select Related khắc phục lỗi N+1 Query.
* **ORM QuerySet**: Tự động tính toán tổng giá trị kho hàng, lọc sản phẩm sắp hết hạn thông qua `F`, `Sum`, và `ExpressionWrapper`.
* **Dashboard Bootstrap**: Giao diện hiển thị trực quan các báo cáo về tình hình kho hàng.

## Yêu cầu môi trường
* Python 3.13+
* `uv` (Nếu chưa cài đặt, hãy cài qua lệnh: `pip install uv`).

## Hướng dẫn cài đặt và chạy chạy dự án

### Bước 1: Clone dự án và di chuyển vào thư mục `day8`
```bash
# Di chuyển vào đúng folder chứa dự án
cd learn/day8-12_django/day8
```

### Bước 2: Kích hoạt môi trường và cài đặt thư viện
Dự án sử dụng `uv` để quản lý môi trường ảo (virtual environment).
```bash
# Đồng bộ và cài đặt các thư viện từ file pyproject.toml / uv.lock
uv sync
```
Môi trường ảo sẽ được tự động tạo trong thư mục `.venv`.

### Bước 3: Áp dụng Migrations (Khởi tạo Cấu trúc CSDL)
Dự án mặc định sử dụng SQLite. Để tiến hành setup các bảng CSDL:
```bash
uv run p manage.py migrate
```

### Bước 4: Khởi tạo dữ liệu giả lập (Tùy chọn)
Nếu bạn muốn có sẵn dữ liệu và tài khoản test để xem, bạn có thể tự tạo siêu người dùng:
```bash
uv run python manage.py createsuperuser
```
### Bước 5: Chạy Máy chủ (Run Server)
```bash
uv run python manage.py runserver
```

## Hướng dẫn sử dụng
* **Dashboard Tổng quan**: Truy cập [http://127.0.0.1:8000/inventory/](http://127.0.0.1:8000/inventory/)
* **Trang Quản trị (Admin)**: Truy cập [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) 
  *(tài khoản : `admin` / mật khẩu `admin`)*
