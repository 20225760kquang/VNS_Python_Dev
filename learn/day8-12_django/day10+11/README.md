# Django E-commerce Backend (Day 10+11)

Day10+11 mở rộng từ day9 thành backend cho hệ thống e-commerce gồm:

- Inventory (quản lý hàng hóa, nhà cung cấp, giao dịch kho)
- Cart (giỏ hàng theo người dùng)
- Order (checkout tạo đơn hàng, trừ tồn kho)
- Celery + Redis (gửi email xác nhận đơn và xử lý ảnh sản phẩm bất đồng bộ)

## Quy tắc nghiệp vụ chính

- Inventory API: public read, staff write.
- Cart/Order API: yêu cầu đăng nhập (`IsAuthenticated`).
- Checkout sử dụng transaction và `F()` update để trừ kho an toàn.
- Khi tạo Order mới: signal `post_save` sẽ enqueue Celery task gửi email xác nhận.
- Khi upload ProductImage mới: signal sẽ enqueue Celery task resize/compress ảnh.

## API endpoints

### Inventory

- `GET /api/inventory/categories/`
- `GET /api/inventory/suppliers/`
- `GET /api/inventory/products/`
- `GET /api/inventory/products/low_stock/`
- `GET /api/inventory/products/summary/`
- `GET /api/inventory/product-images/`
- `GET /api/inventory/transactions/`

### Cart

- `GET /api/cart/` lấy giỏ hàng active của user.
- `POST /api/cart/items/` thêm sản phẩm vào giỏ.
- `PATCH /api/cart/items/{id}/` cập nhật số lượng.
- `DELETE /api/cart/items/{id}/` xóa item.
- `POST /api/cart/checkout/` tạo order từ giỏ hiện tại.

### Orders

- `GET /api/orders/` danh sách đơn hàng.
- `GET /api/orders/{id}/` chi tiết đơn hàng.
- `POST /api/orders/{id}/cancel/` hủy đơn hàng và hoàn lại tồn kho.

### Seed mock data

- Chạy lệnh để tạo dữ liệu mẫu inventory/cart/order:

```bash
uv run python manage.py seed_mock_data --reset
```

- Tài khoản mẫu:
	- `admin_seed / Admin@123` (staff + superuser)
	- `alice / Alice@123`
	- `bob / Bob@12345`

## Demo flow tạo order và nhận được email tự động

Mục tiêu demo: từ 1 user thường, thêm sản phẩm vào giỏ và checkout để tạo ra 1 order mới.

### Thực hiện các bước dưới

1. `GET /api/inventory/products/` để chọn `id` sản phẩm còn hàng.
2. `POST /api/cart/items/` với body:

```json
{
  "product_id": 1,
  "quantity": 1
}
```

3. `GET /api/cart/` để kiểm tra giỏ.
4. `POST /api/cart/checkout/` với body:

```json
{
  "shipping_address": ""
}
```

5. `GET /api/orders/` để xác nhận order mới đã được tạo.

## Chạy dự án

### 1) Cài dependency và migrate

```bash
uv sync
uv run python manage.py migrate
```

### 2) Chạy Redis (bắt buộc cho Celery)

#### Cách 1 - Redis bằng Docker (khuyến nghị)

```bash
docker run -d --name redis-day10+11 -p 6379:6379 redis:7
docker ps
```

Nếu đã tạo container từ trước:

```bash
docker start redis-day10+11
```

Dừng Redis:

```bash
docker stop redis-day10+11
```

#### Cách 2 - Redis local (nếu đã cài redis-server)

```bash
redis-server
```

Terminal khác để kiểm tra:

```bash
redis-cli ping
```
### 3) Chạy Celery worker

```bash
uv run celery -A config worker -l info -P solo
```

### 4) Chạy Django server

```bash
uv run python manage.py runserver
```

### 5) Tạo dữ liệu mẫu và demo tạo order

```bash
uv run python manage.py seed_mock_data --reset
```

## Cấu hình môi trường (tùy chọn)

- File env đặt tại: `.env` (thư mục gốc `day10`). Có mẫu tham khảo trong `.env.example`.
- Sau khi sửa `.env`, hãy restart lại Celery worker và Django server để nạp cấu hình mới.

- `CELERY_BROKER_URL` (default: `redis://127.0.0.1:6379/0`)
- `CELERY_RESULT_BACKEND` (default: `redis://127.0.0.1:6379/1`)
- `EMAIL_BACKEND` (fix: smtp backend) 
- `EMAIL_HOST` (default: `localhost`)
- `EMAIL_PORT` (default: `25`)
- `EMAIL_USE_TLS` (default: `False`)
- `EMAIL_USE_SSL` (default: `False`)
- `EMAIL_HOST_USER` (default: empty)
- `EMAIL_HOST_PASSWORD` (fix: gmail_app_password)
- `EMAIL_TIMEOUT` (default: `15`)
- `DEFAULT_FROM_EMAIL` (default: `noreply@inventory.local`)

- Hãy lấy được gmail_app_password để thêm vào file .env nhé (mã gồm 16 kí tự !)
