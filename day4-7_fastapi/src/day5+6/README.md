# Day5+6 - FastAPI + PostgreSQL + Authentication

## 1. Điểm cải thiện so với Day4

So với Day4, project Day5+6 cải thiện rõ ở 2 phần chính:

1. Chuyển từ dữ liệu giả lưu file `.txt` sang làm việc với **database PostgreSQL**.
2. Bổ sung luồng xác thực người dùng đầy đủ: **đăng ký, đăng nhập, đăng xuất**, thay vì giả định cố định `user_id = 1`.

## 2. Sơ đồ cấu trúc của project khi này

```text
day5+6/
	alembic.ini
	README.md
	requirements.txt
	alembic/
		env.py
		README
		script.py.mako
		versions/
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
			blogs.py
			comments.py
		utils/
			create_mock_data.py
```

### Ý nghĩa từng phần

- `alembic.ini`: cấu hình chung cho Alembic (đường dẫn migration scripts, logging...).
- `alembic/env.py`: file quan trọng để Alembic biết metadata model nào cần migrate và cách chạy migrate (offline/online, async).
- `alembic/script.py.mako`: template tạo file migration mới.
- `alembic/versions/`: nơi chứa các file revision migration (hiện tại có thể đang trống).

- `app/main.py`: entrypoint FastAPI app, đăng ký middleware và include routers.
- `app/database.py`: cấu hình kết nối DB, `engine`, `session_local`, `Base`, dependency `get_db`.
- `app/models.py`: định nghĩa ORM model `User`, `Blog`, `Comment`, quan hệ giữa các bảng.
- `app/schemas.py`: schema request/response bằng Pydantic, gồm validate dữ liệu đầu vào (vd: password).

- `app/core/security.py`: xử lý bảo mật cốt lõi: hash/verify password, tạo JWT, blacklist token cho logout.
- `app/core/dependencies.py`: dependency lấy user hiện tại từ bearer token (decode JWT, truy vấn DB).
- `app/core/middleware.py`: đăng ký các middleware toàn cục (CORS, GZip, request-id/logging, security headers).

- `app/routers/auth.py`: API đăng ký/đăng nhập/token/logout.
- `app/routers/blogs.py`: API CRUD blog, có phân quyền theo chủ sở hữu và trạng thái draft/published.
- `app/routers/comments.py`: API CRUD comment + reply, kiểm tra quyền truy cập theo visibility của blog.

- `app/utils/create_mock_data.py`: script async seed dữ liệu mẫu vào database.

- `requirements.txt`: danh sách thư viện cần cài (FastAPI, SQLAlchemy, asyncpg, alembic, jose, passlib...).

---

## 3. Giải thích yêu cầu kỹ thuật

## 3.1 Kết nối với cơ sở dữ liệu PostgreSQL

### Cách làm trong project

- Đọc `DATABASE_URL` từ `.env`.
- Chuẩn hóa URL về async driver `postgresql+asyncpg://`.
- Khởi tạo `create_async_engine(...)`.

## 3.2 Async/await trong Database

### Cách làm trong project

- Dùng `AsyncSession` và `async_sessionmaker`.
- Dependency `get_db()` là async generator, mở/đóng session theo request.
- Tại router, các thao tác DB đều `await`: `execute`, `commit`, `refresh`, `delete`.

Ý nghĩa: I/O với DB không chặn event loop, phù hợp FastAPI async và tăng khả năng xử lý đồng thời.


## 3.3 Cấu hình Alembic

### Cách làm trong project

- Khai báo script location trong `alembic.ini`.
- Trong `alembic/env.py`:
	- load `.env`
	- đưa `DATABASE_URL` vào `config.set_main_option("sqlalchemy.url", ...)`
	- trỏ `target_metadata = Base.metadata` để autogenerate từ ORM models
	- hỗ trợ async migration bằng `create_async_engine` + `connection.run_sync(...)`

## 3.4 JWT Authentication

### Cách làm trong project

- Khi register/login thành công, hệ thống tạo JWT có payload `sub = user_id`.
- Token có hạn dùng (`exp`) theo biến môi trường `ACCESS_TOKEN_EXPIRE_MINUTES`.
- Mỗi request protected sẽ decode token, lấy `sub`, truy vấn user từ DB.
- Logout được xử lý bằng token blacklist runtime (`REVOKED_TOKENS`).

## 3.5 Middleware áp dụng trong project gồm :

Trong `app/core/middleware.py`, project đang áp dụng:

1. `CORSMiddleware`
2. `GZipMiddleware` (`minimum_size=1024`)
3. Custom request context + logging middleware
4. Security headers trong response

## 3.6 OAuth2

### Cách làm trong project

- Dùng `OAuth2PasswordBearer(tokenUrl="token")` để FastAPI/Swagger hiểu endpoint cấp token.
- Endpoint `/token` nhận `OAuth2PasswordRequestForm` theo chuẩn password flow.
- Sau khi bấm `Authorize` trên Swagger, token bearer được tự động đính vào các API cần `Depends(get_current_user)`.


Ý nghĩa: OAuth2 ở đây là cơ chế chuẩn để client lấy và gửi bearer token; token thực tế được triển khai bằng JWT.

