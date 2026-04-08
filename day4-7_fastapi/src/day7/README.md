# Day7 - FastAPI Advanced: Background Tasks, RBAC, Docker

## 1. Điểm cải thiện so với Day5+6

Day7 cải thiện từ Day5+6 theo 4 hướng chính:

1. Bổ sung `BackgroundTasks` để xử lý một số tác vụ phụ sau khi trả response.
2. Thêm phân quyền theo vai trò (Role-Based Access Control): `normal_user` và `admin`.
3. Viết `Dockerfile` để đóng gói ứng dụng thành image.
4. Viết `docker-compose.yml` để chạy đồng bộ database, migration và API.


## 2. Cấu trúc dự án 

```text
day7/
	.dockerignore
	.env
	.gitignore
	alembic.ini
	Dockerfile
	docker-compose.yml
	requirements.txt
	README.md
	alembic/
		env.py
		README
		script.py.mako
		versions/
			20260408_01_add_user_role.py
	app/
		__init__.py
		database.py
		main.py
		models.py
		schemas.py
		core/
			__init__.py
			dependencies.py
			middleware.py
			security.py
		routers/
			__init__.py
			auth.py
			admin.py
			blogs.py
			comments.py
		utils/
			__init__.py
			create_mock_data.py
```

### Ý nghĩa từng phần

- `Dockerfile`: build image FastAPI app, cài dependencies và chạy `uvicorn`.
- `docker-compose.yml`: orchestrate nhiều service:
	- `database` (PostgreSQL)
	- `migrate` (chạy Alembic migration)
	- `api` (chạy FastAPI)
- `alembic/versions/20260408_01_add_user_role.py`: migration thêm trường role và/hoặc tạo bảng.

- `app/main.py`: khởi tạo FastAPI app, attach middleware, include routers.
- `app/database.py`: cấu hình async engine + session cho PostgreSQL.
- `app/models.py`: định nghĩa bảng `users`, `blogs`, `comments`; có cột `role` ở bảng `users`.
- `app/schemas.py`: schema request/response và enum `UserRole`.

- `app/core/security.py`: hash/verify password, tạo JWT, revoke token.
- `app/core/dependencies.py`: dependency lấy current user và kiểm tra admin (`get_current_admin`).
- `app/core/middleware.py`: CORS, GZip, request logging, security headers.

- `app/routers/auth.py`: register/login/logout, register admin bằng `X-Admin-Key`, có background task.
- `app/routers/admin.py`: các endpoint chỉ admin mới gọi được.
- `app/routers/blogs.py`, `app/routers/comments.py`: nghiệp vụ blog/comment cho user đã xác thực.
- `app/utils/create_mock_data.py`: script seed dữ liệu mẫu.

---

## 3. Giải thích yêu cầu kỹ thuật

## 3.1 Background Tasks

### Mục tiêu

Tách các tác vụ phụ (không bắt buộc phải hoàn tất trước khi trả response) ra khỏi luồng xử lý chính để tăng trải nghiệm người dùng.

### Cách triển khai trong project

- Sử dụng `BackgroundTasks` của FastAPI tại router auth.
- Sau khi tạo user hoặc logout thành công, hệ thống thêm task vào hàng đợi background bằng `background_tasks.add_task(...)`.
- Các task cụ thể:
	- `send_welcome_notification(email, name)` ghi log thông báo welcome.
	- `write_logout_audit(user_id)` ghi log audit logout.

## 3.2 Phân quyền (Role-Based Access Control - RBAC)

### Vai trò trong hệ thống

- `normal_user`: người dùng thường.
- `admin`: người dùng quản trị.

### Cách triển khai trong project

1. Thêm cột `role` trong model user:
	 - `app/models.py`: `role = Column(String, nullable=False, default="normal_user", ...)`
2. Thêm enum role trong schema:
	 - `app/schemas.py`: `class UserRole(str, Enum): normal_user, admin`
3. Tạo dependency kiểm tra admin:
	 - `app/core/dependencies.py`: `get_current_admin` raise `403` nếu role khác `admin`.
4. Áp dụng vào admin endpoints:
	 - `app/routers/admin.py`: `Depends(get_current_admin)` ở các API quản trị.
5. Đưa role vào JWT payload:
	 - `app/routers/auth.py`: payload chứa `{"sub": ..., "role": ...}` khi login/register.
6. Bảo vệ luồng tạo admin:
	 - endpoint register admin yêu cầu header `X-Admin-Key` khớp `ADMIN_REGISTER_KEY`.

### Các endpoint được bổ sung

- `GET /admin/users`: xem toàn bộ user.
- `PATCH /admin/users/{user_id}/role`: đổi role user.
- `GET /admin/users/{user_id}/blogs-all`: xem toàn bộ blog của user (kể cả draft), có filter ngày.


## 4. Chạy Docker Compose

### Cách chạy

```bash
docker compose up --build
```

Compose sẽ tự:

1. Khởi động service `database`.
2. Đợi DB healthy.
3. Chạy service `migrate` với lệnh `alembic upgrade head`.
4. Sau khi migrate thành công mới chạy service `api`.

Swagger: `http://localhost:8000/docs`

### Chạy nền

```bash
docker compose up -d --build
```

### Dừng và xóa container/network

```bash
docker compose down
```

### Dừng và xóa cả volume data DB

```bash
docker compose down -v
```

---

## 5. Checklist biến môi trường cần có

Đảm bảo file `.env` có các biến tối thiểu:

- `DATABASE_URL`
- `SECRET_KEY`
- `ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `ADMIN_REGISTER_KEY`
- (tuỳ chọn) `CORS_ALLOW_ORIGINS`

Lưu ý khi chạy bằng Compose: giá trị host trong `DATABASE_URL` nên trỏ tới service DB trong compose (thường là `database`) thay vì `localhost`.

---

