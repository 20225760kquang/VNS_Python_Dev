# Django E-commerce Backend (hoàn thiện)

## Yêu cầu kĩ thuật được bổ sung

- Bổ sung các API endpoint về Authentication (login,logout,register)
- Phân quyền theo role (admin & normal user)
- Viết Unit Test (gồm các edge cases cho từng module tổng cộng là 27 unit tests)
- Chạy project qua Docker Compose ! 

## Chạy dự án với Docker Compose (khuyến khích)

Khởi động toàn bộ services:

```bash
docker compose up --build
```

Chạy nền:

```bash
docker compose up -d --build
```

Dừng và xóa container/network:

```bash
docker compose down
```

Sau khi các services chạy xong:

- Django web: `http://127.0.0.1:8000`
- Redis: `127.0.0.1:6379`

`docker-compose.yml` gồm các service:

- `redis`: broker cho Celery
- `migrate`: chạy migration trước khi app start
- `web`: Django server
- `worker`: Celery worker



## Chạy dự án 

### 1) Cài dependency và migrate

```bash
uv sync
uv run python manage.py migrate
```

Lưu ý: app auth dùng DRF TokenAuthentication nên migration `authtoken` cần được áp dụng (lệnh migrate ở trên đã bao gồm).

### 2) Chạy Redis (bắt buộc cho Celery)

#### Cách 1 - Redis bằng Docker (khuyến nghị)

```bash
docker run -d --name redis-django -p 6379:6379 redis:7
docker ps
```

Nếu đã tạo container từ trước:

```bash
docker start redis-django
```

Dừng Redis:

```bash
docker stop redis-django
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

## Unit Test & Clean Code

Project đã tích hợp `pytest`, `pytest-django`, `pytest-mock` và `ruff`.

### Chạy toàn bộ unit test

```bash
uv run pytest
```

### Chạy test theo module

```bash
uv run pytest auth/test_auth_pytest.py
uv run pytest cart/test_cart_pytest.py
uv run pytest inventory/test_inventory_pytest.py
uv run pytest orders/test_orders_pytest.py
```

### Kiểm tra Clean Code (PEP8/Ruff)

```bash
uv run ruff check .
uv run ruff format .
```

## Cấu hình biến môi trường (tùy chọn)

- File env đặt tại: `.env` (thư mục gốc `day12+13`). Có mẫu tham khảo trong `.env.example`.
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
