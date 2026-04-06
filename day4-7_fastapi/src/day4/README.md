# Day 4 FastAPI Blog & Comment Mock App

## Tổng quan

Dự án này là một ứng dụng FastAPI nhỏ dùng để thực hành các use case liên quan đến blog và comment.
Hiện tại ứng dụng đang làm việc với dữ liệu giả được lưu trong các file text, chưa kết nối với cơ sở dữ liệu thật.

Chưa có luồng xác thực hay đăng ký/đăng nhập.
Tất cả API đều giả lập người dùng hiện tại là user có `user_id = 1`.

## Phạm vi hiện tại

- Quản lý blog với các thao tác tạo, xem, sửa và xóa.
- Quản lý comment với các thao tác tạo, reply, xem, sửa và xóa.
- Lưu trữ dữ liệu thông qua các file `.txt` mock data.
- Các model SQLAlchemy hiện chỉ được dùng như object dữ liệu trong bộ nhớ.

## Quy tắc nghiệp vụ

- Khi tạo hoặc cập nhật blog, ứng dụng tự động set `published_at` và `updated_at` theo trạng thái.
- Khi tạo hoặc cập nhật comment, `updated_at` sẽ do server tự xử lý.
- Người dùng chỉ được sửa hoặc xóa blog/comment của chính mình.
- Blog ở trạng thái draft chỉ chủ sở hữu mới được xem.
- Khi xóa blog, các comment liên quan cũng được xóa khỏi file mock data.

## Use case

### Use case của blog

1. Tạo blog mới.
2. Xem một blog.
3. Xem toàn bộ blog của một người dùng.
4. Sửa một blog.
5. Xóa một blog.

### Use case của comment

1. Tạo comment cho một blog.
2. Reply vào một comment đã có.
3. Xem danh sách comment của một blog.
4. Xem một comment.
5. Sửa một comment.
6. Xóa một comment.

## Mô hình dữ liệu

### User

- `user_id`: khóa chính
- `name`
- `email`
- `hashed_password`
- `created_at`

### Blog

- `blog_id`: khóa chính
- `title`
- `content`
- `created_at`
- `status`: `draft` hoặc `published`
- `published_at`
- `updated_at`
- `author_id`: khóa ngoại trỏ tới `users.user_id`

### Comment

- `comment_id`: khóa chính
- `user_id`: khóa ngoại trỏ tới `users.user_id`
- `blog_id`: khóa ngoại trỏ tới `blogs.blog_id`
- `parent_id`: tự tham chiếu tới `comments.comment_id` để hỗ trợ reply
- `content`
- `created_at`
- `updated_at`

### Mô hình quan hệ

- Một user có thể sở hữu nhiều blog.
- Một user có thể viết nhiều comment.
- Một blog có thể có nhiều comment.
- Một comment có thể có nhiều comment reply.

## Cây thư mục dự án

```text
day4/
├── main.py
├── models.py
├── schemas.py
├── README.md
├── requirements.txt
├── mock_data/
│   ├── account.txt
│   ├── blogs.txt
│   └── comments.txt
├── routers/
│   ├── blogs.py
│   └── comments.py
└── utils/
	├── load_txt.py
	└── save_txt.py
```

## Ý nghĩa từng file

- `main.py`: điểm khởi chạy ứng dụng. Hiện tại file này đang trống và sẽ dùng để tạo và chạy FastAPI app.
- `models.py`: định nghĩa các model ORM SQLAlchemy cho `User`, `Blog` và `Comment`.
- `schemas.py`: định nghĩa schema Pydantic cho request/response của blog và comment.
- `routers/blogs.py`: chứa các route và logic nghiệp vụ cho blog dựa trên mock data.
- `routers/comments.py`: chứa các route và logic nghiệp vụ cho comment dựa trên mock data.
- `utils/load_txt.py`: đọc dữ liệu giả từ file `.txt` và chuyển thành object trong bộ nhớ.
- `utils/save_txt.py`: ghi dữ liệu blog/comment đã cập nhật trở lại file `.txt`.
- `mock_data/account.txt`: dữ liệu giả của user.
- `mock_data/blogs.txt`: dữ liệu giả của blog.
- `mock_data/comments.txt`: dữ liệu giả của comment.
- `requirements.txt`: danh sách package tối thiểu cần cài để chạy dự án.

## Định dạng dữ liệu nguồn

Ứng dụng hiện tại đọc và ghi các file text sau:

- `account.txt`
- `blogs.txt`
- `comments.txt`

Mỗi file dùng định dạng các cột được ngăn cách bằng dấu `|` và có một dòng header ở đầu file.

## Cách chạy

1. Cài các package trong `requirements.txt`.
2. Khởi động FastAPI application sau khi `main.py` được hoàn thiện.
3. Dùng Swagger UI để test các endpoint blog và comment.

## Các loại Parameter trong FastAPI

Trong dự án này, các API có thể nhận nhiều kiểu tham số khác nhau. Dưới đây là ý nghĩa của từng loại:

### Path Parameter

- Nằm trong đường dẫn URL.
- Thường dùng để định danh tài nguyên cụ thể như blog hoặc comment.
- Ví dụ: `/blogs/{blog_id}`, `/comments/{comment_id}`.
- Trong dự án này, `blog_id`, `comment_id`, `user_id` là các path parameter phổ biến.

### Query Parameter

- Nằm sau dấu `?` trong URL.
- Thường dùng cho phân trang, lọc, sắp xếp hoặc tìm kiếm.
- Ví dụ: `/blogs?page=1&limit=10`.
- Trong dự án này, `page` và `limit` được dùng để phân trang danh sách blog/comment.

### Header Parameter

- Nằm trong header của request HTTP.
- Thường dùng để truyền metadata như token, ngôn ngữ, định dạng dữ liệu.
- Ví dụ: `Authorization`, `X-Request-Id`, `Accept-Language`.
- Hiện tại dự án chưa dùng auth nên chưa có header bắt buộc, nhưng có thể bổ sung sau này khi thêm đăng nhập.

### Cookie Parameter

- Nằm trong cookie mà trình duyệt gửi kèm request.
- Thường dùng để lưu session hoặc thông tin người dùng trên client.
- Hiện tại dự án chưa dùng cookie vì chưa có xác thực và session.
- Sau này nếu thêm login session thì cookie có thể dùng để lưu trạng thái đăng nhập.


